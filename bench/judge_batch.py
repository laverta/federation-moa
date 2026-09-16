# -*- coding: utf-8 -*-
"""judge_batch.py — 批量判卷（固定工作区防 DLL 拦截 + 失败重试）"""
import json, os, subprocess, sys, tempfile, shutil
from pathlib import Path

sys.path.insert(0, REPO_ROOT / "bench")
from bcb_hard import extract_completion

HERE = Path(REPO_ROOT / "bench")
VENV_PY = HERE / ".venv_bcb" / "Scripts" / "python.exe"
BANK = {json.loads(l)["task_id"]: json.loads(l) for l in (HERE / "bcb_hard.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
WS = HERE / ".judge_ws"


def judge_fixed(pb, completion):
    lines = completion.splitlines()
    variants = [completion]
    if lines and lines[0] and not lines[0][0].isspace():
        variants.append("\n".join(("    " + l) if l.strip() else l for l in lines))
    WS.mkdir(exist_ok=True)
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")
    last = ""
    for attempt in range(2):  # DLL 策略拦截间歇性，重试一次
        sub = WS / f"run_{attempt}.py"
        for v in variants:
            src = pb["complete_prompt"] + v + "\n\n" + pb["test"] + "\nif __name__ == '__main__':\n    unittest.main()\n"
            sub.write_text(src, encoding="utf-8")
            try:
                p = subprocess.run([str(VENV_PY), str(sub)], capture_output=True, text=True,
                                   timeout=30, cwd=str(WS), env=env)
                if p.returncode == 0:
                    return True, ""
                last = (p.stderr or p.stdout or "")[-250:]
            except subprocess.TimeoutExpired:
                last = "timeout"
        shutil.rmtree(WS, ignore_errors=True)
        WS.mkdir(exist_ok=True)
    return False, last


rows = [json.loads(l) for l in (HERE / "bcb_exam" / "answers.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
results, p, n = [], 0, 0
for r in rows:
    comp = r.get("completion", "")
    if not comp.strip():
        continue
    pb = BANK.get(r["task_id"])
    if not pb:
        continue
    ok, err = judge_fixed(pb, comp)
    p += ok; n += 1
    results.append({"task_id": r["task_id"], "gm38": ok})
    print(f"[{'PASS' if ok else 'FAIL'}] {r['task_id']}" + ("" if ok else " | " + (err or "")[-70:].replace("\n", " ")))

(HERE / "bcb_exam" / "gm38_judged.json").write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
print(f"\n== Gemini 3.8 flash 已判 {n} 题: {p}/{n} = {p/n*100:.0f}% ==")
