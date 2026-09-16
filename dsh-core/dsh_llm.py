# -*- coding: utf-8 -*-
"""
dsh_llm.py — DSH L2 认知推理适配器（DeepSeek · RFC-001 v1.1.0 Phase 4 · FM-06/12）

纯标准库 urllib 调用（Zero-Dependency 铁律）；key 只从外部路径读取，绝不复制入库（不入 git 台账）。
断路器：连续 BREAKER_N 次配额类报错 → 全局 TRIPPED → 降级 DEGRADED_FILE_ONLY（等重置窗口自动复位）。
用法：
  py dsh_llm.py --ask "问题"          # 单次问答（首单联调用）
  py dsh_llm.py --selftest            # 断路器状态机 + 请求构造（不真调 API，零消耗）
"""
from __future__ import annotations

import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # FM-07
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

KEY_PATH = None  # key 改为环境变量 DEEPSEEK_API_KEY  # key 唯一物理源（指挥官置放）
KEY_PATH_GEMINI = None  # GEMINI_API_KEY
ENDPOINT = os.environ.get("DSH_LLM_ENDPOINT", "https://api.deepseek.com/chat/completions")
MODEL = os.environ.get("DSH_LLM_MODEL", "deepseek-chat")
PROVIDER = os.environ.get("DSH_LLM_PROVIDER", "deepseek")  # deepseek | gemini（MOA 选角开关）
GEMINI_MODEL = os.environ.get("DSH_LLM_GEMINI_MODEL", "gemini-3.8-flash")
PROXY = os.environ.get("DSH_LLM_PROXY", "http://127.0.0.1:9876")  # Gemini 出海必经
BREAKER_N = 2          # FM-12：连续 2 次配额类报错即熔断
BREAKER_COOLDOWN = 600 # 熔断冷却（对齐 LEASE_TTL，等重置窗口）
MAX_CYCLE_STEPS = 15   # FM-06：单工单步长配额
QUOTA_MARKS = ("quota", "429", "rate limit", "ratelimit", "5h limit", "insufficient_balance")
SYSTEM_PROMPT = ("你是联邦 DSH 席位（新 DSH 内核，宿主于 Windows 单机）。"
                 "回答精炼、工程化、中文。收到工单按署名块格式给出结论。")


class CircuitBreaker:
    """FM-12 池级断路器：CLOSED → TRIPPED →（冷却后）CLOSED。"""

    def __init__(self):
        self.fails = 0
        self.tripped_at = 0.0

    @property
    def state(self) -> str:
        if self.fails >= BREAKER_N and time.time() - self.tripped_at < BREAKER_COOLDOWN:
            return "TRIPPED"
        return "CLOSED"

    def record(self, err: str) -> bool:
        """记录一次调用错误；返回 True 表示应熔断。非配额类错误计数衰减。"""
        low = err.lower()
        if any(m in low for m in QUOTA_MARKS):
            self.fails += 1
            if self.fails >= BREAKER_N:
                self.tripped_at = time.time()
                return True
        else:
            self.fails = 0
        return False

    def reset(self) -> None:
        self.fails = 0


_breaker = CircuitBreaker()


def load_key() -> str:
    k = os.environ.get("DEEPSEEK_API_KEY", "")
    if not k:
        raise RuntimeError("DEEPSEEK_API_KEY not set (see .env.example)")
    return k


def _chat_gemini(messages: list) -> str:
    """Gemini generateContent：messages → contents+systemInstruction；出海走本机代理。"""
    sys_text = "\n".join(m["content"] for m in messages if m.get("role") == "system")
    contents = [{"role": ("user" if m.get("role") != "assistant" else "model"),
                 "parts": [{"text": m["content"]}]}
                for m in messages if m.get("role") in ("user", "assistant")]
    body = json.dumps({"contents": contents,
                       "systemInstruction": {"parts": [{"text": sys_text}]} if sys_text else None,
                       "generationConfig": {"temperature": 0.0, "maxOutputTokens": 2048}}).encode("utf-8")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={os.environ.get('GEMINI_API_KEY', '')}")
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    px = {"http": PROXY, "https": PROXY}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler(px))
    try:
        with opener.open(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        _breaker.reset()
        return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        if _breaker.record(f"{e.code} {detail}"):
            raise RuntimeError(f"BREAKER TRIPPED ({e.code}): {detail}") from e
        raise


def chat(prompt: str, history: list | None = None, steps: int = 0) -> str:
    """单轮/多轮对话。步长超限抛 RuntimeError（FM-06）；熔断态直接拒绝调用（FM-12）。
    provider 由 DSH_LLM_PROVIDER 选角（deepseek 默认 | gemini），断路器两池共用。"""
    if steps > MAX_CYCLE_STEPS:
        raise RuntimeError(f"BLOCKED: step budget exceeded ({MAX_CYCLE_STEPS})")
    if _breaker.state == "TRIPPED":
        raise RuntimeError("BLOCKED: quota breaker TRIPPED, DSH in DEGRADED_FILE_ONLY")
    has_system = any(isinstance(m, dict) and m.get("role") == "system" for m in (history or []))
    sys_list = [] if has_system else [{"role": "system", "content": SYSTEM_PROMPT}]
    messages = sys_list + (history or []) + [{"role": "user", "content": prompt}]
    if PROVIDER == "gemini":
        return _chat_gemini(messages)
    body = json.dumps({"model": MODEL, "messages": messages, "max_tokens": 2048, "stream": False}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {load_key()}",
    })
    try:
        # api.deepseek.com is domestic; bypass system proxy for direct high-speed connection
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        _breaker.reset()
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        if _breaker.record(f"{e.code} {detail}"):
            raise RuntimeError(f"BREAKER TRIPPED ({e.code}): {detail}") from e
        raise
    except urllib.error.URLError as e:
        if _breaker.record(str(e.reason)):
            raise RuntimeError(f"BREAKER TRIPPED (network): {e.reason}") from e
        raise


# ---------------- selftest（零 API 消耗） ----------------
def _selftest() -> int:
    b = CircuitBreaker()
    assert b.state == "CLOSED"
    assert not b.record("普通网络抖动 timeout"), "非配额错误不应熔断"
    assert not b.record("HTTP 429 too many requests"), "第一次配额错误只计数"
    assert b.record("quota_exceeded for this key"), "连续第二次配额错误应熔断"
    assert b.state == "TRIPPED", "应进入 TRIPPED"
    b.tripped_at -= BREAKER_COOLDOWN + 1
    assert b.state == "CLOSED", "冷却期满应自动复位"
    key = load_key()
    assert key.startswith("sk-") and len(key) > 20, "key 文件读取异常"
    assert MAX_CYCLE_STEPS == 15
    print("[SELFTEST] dsh_llm PASS: breaker CLOSED->TRIPPED->cooldown-reset, quota marks, key file ok")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ask", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(_selftest())
    if a.ask:
        print(chat(a.ask))
        sys.exit(0)
    sys.exit(0)
