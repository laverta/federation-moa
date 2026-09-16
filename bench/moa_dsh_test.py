# -*- coding: utf-8 -*-
"""moa_dsh_test.py — DSH 通道 MOA 实测：3 道双错题投单（daemon 已切 Gemini 提供方）→ 回执 → 判卷。"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bcb_hard import judge, extract_completion

DSH = Path(REPO_ROOT / "dsh-core")
HERE = Path(__file__).resolve().parent
bank = {json.loads(l)["task_id"]: json.loads(l) for l in (HERE / "bcb_hard.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
targets = json.load(open(HERE / "bcb_exam" / "moa_dsh_3.json", encoding="utf-8"))

cursor = json.loads((DSH / "cursor.json").read_text(encoding="utf-8"))
base = cursor.get("acked_seq", 0)
lines = []
for i, tid in enumerate(targets):
    prompt = ("Complete the following Python function. Reply with ONLY the code, no explanations.\n\n"
              + bank[tid]["complete_prompt"])
    body = {"task_id": f"MOA-DSH-{i:02d}", "msg_type": "TASK", "seq": base + 1 + i,
            "sender": "zcode", "recipient": "dsh", "topic": "FED-BENCH-001", "created_at": time.time()}
    payload = {"summary": prompt}
    body["checksum"] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    body["payload"] = payload
    lines.append(json.dumps(body, ensure_ascii=False))
with open(DSH / "INBOX.ndjson", "a", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(f"已投 3 单（seq {base+1}-{base+3}，provider=gemini），等待回执…")

want = {f"MOA-DSH-{i:02d}": tid for i, tid in enumerate(targets)}
answers, deadline = {}, time.time() + 600
while time.time() < deadline and len(answers) < len(want):
    time.sleep(8)
    for l in (DSH / "OUTBOX.ndjson").read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        try:
            m = json.loads(l)
        except json.JSONDecodeError:
            continue
        tid = m.get("task_id", "")
        if tid in want and tid not in answers:
            answers[tid] = m.get("payload", {}).get("answer", "")

p = 0
for i, tid in enumerate(targets):
    key = f"MOA-DSH-{i:02d}"
    if key not in answers:
        print(f"[超时] {tid}")
        continue
    ok, err = judge(bank[tid], extract_completion(answers[key]))
    p += ok
    print(f"[{'PASS' if ok else 'FAIL'}] {tid} via DSH×Gemini" + ("" if ok else " | " + (err or "")[-70:].replace("\n", " ")))
n = len(answers)
if n:
    print(f"\n== DSH×Gemini 通道: {p}/{n} ==")
    json.dump({want[k]: v for k, v in answers.items()}, open(HERE / "bcb_exam" / "moa_dsh_answers.json", "w", encoding="utf-8"), ensure_ascii=False)
