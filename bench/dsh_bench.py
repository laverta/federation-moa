# -*- coding: utf-8 -*-
"""
dsh_bench.py — DSH 主机实战首测：HumanEval 10 题工单化投递
投单(INBOX.ndjson 信封) → dsh_daemon 处理 → dsh_llm(DeepSeek) 推理 → OUTBOX 回执 → 本地沙箱判定。
用法: py dsh_bench.py          # 投单并等待回执，出判定
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DSH = Path(REPO_ROOT / "dsh-core")
HERE = Path(__file__).resolve().parent
N_QUESTIONS = 10

def envelope(seq: int, task_id: str, summary: str) -> str:
    import hashlib
    body = {"task_id": task_id, "msg_type": "TASK", "seq": seq, "sender": "zcode",
            "recipient": "dsh", "topic": "FED-BENCH-001", "created_at": time.time()}
    payload_canonical = json.dumps({"summary": summary}, ensure_ascii=False, sort_keys=True)
    body["checksum"] = hashlib.sha256(payload_canonical.encode()).hexdigest()[:16]
    body["payload"] = {"summary": summary}
    return json.dumps(body, ensure_ascii=False)

def extract_code(answer: str) -> str:
    if "```" in answer:
        blocks = answer.split("```")
        for i in range(1, len(blocks), 2):
            b = blocks[i]
            if b.startswith("python"):
                b = b[6:]
            if "def " in b:
                return b
    return answer

def judge(pb: dict, code: str) -> bool:
    src = pb["prompt"] + "\n" + code + "\n" + pb["test"] + f"\ncheck({pb['entry_point']})\nprint('ALL_OK')\n"
    try:
        p = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True, timeout=10, cwd=str(HERE))
        return p.returncode == 0 and "ALL_OK" in (p.stdout or "")
    except subprocess.TimeoutExpired:
        return False

def main() -> int:
    problems = [json.loads(l) for l in (HERE / "HumanEval.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()][:N_QUESTIONS]
    cursor = json.loads((DSH / "cursor.json").read_text(encoding="utf-8"))
    base_seq = cursor.get("acked_seq", 0)
    print(f"DSH cursor acked_seq={base_seq}，投 {len(problems)} 单（seq {base_seq+1}..{base_seq+len(problems)}）")

    lines = []
    for i, pb in enumerate(problems):
        prompt = ("Complete the following Python function. Reply with ONLY the code, no explanations.\n\n" + pb["prompt"])
        lines.append(envelope(base_seq + 1 + i, f"DSH-BENCH-{i:02d}", prompt))
    with open(DSH / "INBOX.ndjson", "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("已投单，等待 DSH 处理（daemon 轮询+DeepSeek 推理）…")

    want = {f"DSH-BENCH-{i:02d}" for i in range(len(problems))}
    deadline = time.time() + 900
    results = {}
    while time.time() < deadline and len(results) < len(want):
        time.sleep(10)
        if (DSH / "OUTBOX.ndjson").exists():
            for l in (DSH / "OUTBOX.ndjson").read_text(encoding="utf-8").splitlines():
                if not l.strip():
                    continue
                try:
                    m = json.loads(l)
                except json.JSONDecodeError:
                    continue
                tid = m.get("task_id", "")
                if tid in want and tid not in results:
                    ans = m.get("payload", {}).get("answer", "")
                    results[tid] = ans
                    print(f"  回执 {tid}（{len(ans)}B）")
    if len(results) < len(want):
        print(f"超时：仅 {len(results)}/{len(want)} 回执"); 

    passed = 0
    for i, pb in enumerate(problems):
        tid = f"DSH-BENCH-{i:02d}"
        if tid not in results:
            continue
        ok = judge(pb, extract_code(results[tid]))
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {pb['task_id']} via DSH")
    n = len(results)
    if n:
        print(f"\n== DSH 通道（DeepSeek 经 dsh_llm）: {passed}/{n} = {passed/n*100:.0f}% ==")
    return 0

if __name__ == "__main__":
    sys.exit(main())
