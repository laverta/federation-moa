# -*- coding: utf-8 -*-
"""
llm_bench.py — 联邦 LLM 轻量评测器（HumanEval pass@1）

用法:
  py llm_bench.py --model deepseek --limit 20     # 冒烟 20 题
  py llm_bench.py --model deepseek                # 全量 164 题（断点续跑）
  py llm_bench.py --model gemini --limit 20
纯标准库。逐题落盘 results_<model>.jsonl，中断可续。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
import os
REPO_ROOT = Path(os.environ.get('FEDERATION_ROOT', Path(__file__).resolve().parents[1]))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
DATASET = HERE / "HumanEval.jsonl"
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

# DeepSeek 国内直连（禁代理）；Gemini 必须走本机代理
DS_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
PX = {"http": "http://127.0.0.1:9876", "https": "http://127.0.0.1:9876"}
GM_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler(PX))

MODELS = {
    "deepseek": {"api": "ds", "name": "deepseek-chat"},
    "gemini": {"api": "gm", "name": "gemini-3.8-flash"},
}


def gen_deepseek(prompt: str, model: str) -> str:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0, "max_tokens": 1024,
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_KEY}"})
    with DS_OPENER.open(req, timeout=90) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def gen_gemini(prompt: str, model: str) -> str:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={GEMINI_KEY}")
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 2048},
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with GM_OPENER.open(req, timeout=90) as r:
        d = json.loads(r.read())
        return "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])


def extract_code(reply: str) -> str:
    """提取 ```python 块；若无围栏则整体视为代码（去掉开头说明行）。"""
    if "```" in reply:
        blocks = reply.split("```")
        for i in range(1, len(blocks), 2):
            b = blocks[i]
            if b.startswith("python"):
                b = b[6:]
            if "def " in b:
                return b
        return blocks[1] if len(blocks) > 1 else reply
    return reply


def run_case(problem: dict, code: str) -> tuple[bool, str]:
    """组合 prompt+生成代码+官方测试，子进程执行判定（标准 check(candidate) 协议）。"""
    src = (problem["prompt"] + "\n" + code + "\n" + problem["test"]
           + f"\ncheck({problem['entry_point']})\nprint('ALL_OK')\n")
    try:
        p = subprocess.run([sys.executable, "-c", src], capture_output=True,
                           text=True, timeout=10, cwd=str(HERE))
        return p.returncode == 0 and "ALL_OK" in (p.stdout or ""), (p.stderr or p.stdout)[-300:]
    except subprocess.TimeoutExpired:
        return False, "timeout"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(MODELS))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cfg = MODELS[args.model]
    gen = gen_deepseek if cfg["api"] == "ds" else gen_gemini
    problems = [json.loads(l) for l in DATASET.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limit:
        problems = problems[:args.limit]

    resfile = HERE / f"results_{args.model}.jsonl"
    done = set()
    if resfile.exists():
        for l in resfile.read_text(encoding="utf-8").splitlines():
            if l.strip():
                done.add(json.loads(l)["task_id"])

    passed = total = 0
    for pb in problems:
        if pb["task_id"] in done:
            continue
        prompt = ("Complete the following Python function. Reply with ONLY the code, "
                  "no explanations.\n\n" + pb["prompt"])
        t0 = time.time()
        try:
            reply = gen(prompt, cfg["name"])
        except Exception as e:
            print(f"[ERR] {pb['task_id']} API: {str(e)[:120]}")
            time.sleep(2)
            continue
        code = extract_code(reply)
        ok, err = run_case(pb, code)
        total += 1
        passed += ok
        with open(resfile, "a", encoding="utf-8") as f:
            f.write(json.dumps({"task_id": pb["task_id"], "ok": ok,
                                "secs": round(time.time() - t0, 1)}, ensure_ascii=False) + "\n")
        print(f"[{'PASS' if ok else 'FAIL'}] {pb['task_id']} ({time.time()-t0:.1f}s)" + (f" | {err[:80]}" if not ok and err else ""))

    # 汇总（含已续跑的）
    if resfile.exists():
        rows = [json.loads(l) for l in resfile.read_text(encoding="utf-8").splitlines() if l.strip()]
        p = sum(r["ok"] for r in rows)
        print(f"\n== {args.model} ({cfg['name']}): {p}/{len(rows)} pass@1 = {p/len(rows)*100:.1f}% ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
