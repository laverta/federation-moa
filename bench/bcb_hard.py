# -*- coding: utf-8 -*-
"""
bcb_hard.py — BigCodeBench-Hard 148 题实测（轻量自建 harness）
模式：complete_prompt 续写 → 拼官方 unittest test → 隔离子进程判定（exit 0 = pass）
判定边界声明：轻量判定，不含官方 sanitize/防作弊 syncheck；结果偏乐观或偏悲观均可能，横向对比（同管道同题）有效。
用法: py bcb_hard.py --model deepseek --limit 3   # 冒烟
      py bcb_hard.py --model deepseek             # 全量（断点续跑）
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(os.environ.get('FEDERATION_ROOT', Path(__file__).resolve().parents[1]))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
DATASET = HERE / "bcb_hard.jsonl"
VENV_PY = HERE / ".venv_bcb" / "Scripts" / "python.exe"   # 判定用（依赖齐全）
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

DS_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
GM_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler(
    {"http": "http://127.0.0.1:9876", "https": "http://127.0.0.1:9876"}))
MODELS = {"deepseek": ("ds", "deepseek-chat"), "gemini": ("gm", "gemini-3.8-flash")}


def gen(prompt: str, api: str, model: str) -> str:
    if api == "ds":
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                           "temperature": 0.0, "max_tokens": 4096}).encode()
        req = urllib.request.Request("https://api.deepseek.com/chat/completions", data=body,
                                     method="POST", headers={"Content-Type": "application/json",
                                                             "Authorization": f"Bearer {DEEPSEEK_KEY}"})
        with DS_OPENER.open(req, timeout=180) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"temperature": 0.0, "maxOutputTokens": 8192}}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with GM_OPENER.open(req, timeout=180) as r:
        d = json.loads(r.read())
        return "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])


def extract_completion(reply: str) -> str:
    """模型回复 → 续写段：优先取 ```python 围栏内（去围栏）；否则整体。"""
    if "```" in reply:
        blocks = reply.split("```")
        best = ""
        for i in range(1, len(blocks), 2):
            b = blocks[i]
            if b.startswith("python"):
                b = b[6:]
            if len(b) > len(best):
                best = b
        if best.strip():
            return best
    return reply


def judge(pb: dict, completion: str) -> tuple[bool, str]:
    """双版判定：原样拼接 / 顶格续写整体加 4 空格缩进（complete 模式 chat 模型常见形态），
    任一版本通过即 PASS——轻量容错，结果注明。"""
    variants = [completion]
    lines = completion.splitlines()
    if lines and lines[0] and not lines[0][0].isspace():
        variants.append("\n".join(("    " + l) if l.strip() else l for l in lines))
    last_err = ""
    for v in variants:
        src = pb["complete_prompt"] + v + "\n\n" + pb["test"] + (
            "\nif __name__ == '__main__':\n    unittest.main()\n")
        with tempfile.TemporaryDirectory(dir=str(HERE)) as td:
            fp = Path(td) / "submission_test.py"
            fp.write_text(src, encoding="utf-8")
            env = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")
            try:
                p = subprocess.run([str(VENV_PY), str(fp)], capture_output=True, text=True,
                                   timeout=30, cwd=td, env=env)
                if p.returncode == 0:
                    return True, ""
                last_err = (p.stderr or p.stdout or "")[-250:]
            except subprocess.TimeoutExpired:
                last_err = "timeout>30s"
    return False, last_err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(MODELS))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    api, name = MODELS[args.model]

    problems = [json.loads(l) for l in DATASET.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limit:
        problems = problems[:args.limit]
    resfile = HERE / f"results_bcb_{args.model}.jsonl"
    done = set()
    if resfile.exists():
        done = {json.loads(l)["task_id"] for l in resfile.read_text(encoding="utf-8").splitlines() if l.strip()}

    for pb in problems:
        if pb["task_id"] in done:
            continue
        prompt = ("You are continuing the BODY of a Python function (its signature and docstring are given). "
                  "Reply with ONLY the continuation code indented 4 spaces (inside the function body), "
                  "plus any module-level code after it if needed. No explanations, no markdown fences.\n\n"
                  + pb["complete_prompt"])
        t0 = time.time()
        try:
            reply = gen(prompt, api, name)
        except Exception as e:
            print(f"[ERR] {pb['task_id']} API: {str(e)[:100]}")
            time.sleep(3)
            continue
        ok, err = judge(pb, extract_completion(reply))
        with open(resfile, "a", encoding="utf-8") as f:
            f.write(json.dumps({"task_id": pb["task_id"], "ok": ok,
                                "secs": round(time.time() - t0, 1)}, ensure_ascii=False) + "\n")
        print(f"[{'PASS' if ok else 'FAIL'}] {pb['task_id']} ({time.time()-t0:.0f}s)" + (f" | {err[-90:]}" if not ok else ""))

    if resfile.exists():
        rows = [json.loads(l) for l in resfile.read_text(encoding="utf-8").splitlines() if l.strip()]
        p = sum(r["ok"] for r in rows)
        print(f"\n== BCB-Hard {args.model}: {p}/{len(rows)} = {p/len(rows)*100:.1f}% ==")
    else:
        print(f"\n== BCB-Hard {args.model}: 无结果（通道未通或全部失败）==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
