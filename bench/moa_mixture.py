# -*- coding: utf-8 -*-
"""
moa_mixture.py — MOA（Mixture of Agents）混合解题聚合引擎
输入：同一批题的多份模型答案（answers_*.jsonl）→ 统一判定 → 三级对照：
  1) 单模型各自分；2) MOA-pass@k（任一通过即联合通过）；3) 失败题清单（供旗舰仲裁层加跑）。
用法: py moa_mixture.py --exam-dir bench/solutions --answers answers_*.jsonl
依赖: bcb_hard.py 的 judge 管道（同判定，横向可比）。
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
import os
REPO_ROOT = Path(os.environ.get('FEDERATION_ROOT', Path(__file__).resolve().parents[1]))

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bcb_hard import judge, extract_completion  # 同管道判定

HERE = Path(__file__).resolve().parent


def load_answers(path: Path) -> dict[str, str]:
    out = {}
    for l in path.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            out[r["task_id"]] = r.get("completion", "")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exam-dir", required=True)
    ap.add_argument("--answers", nargs="+", required=True, help="answers_*.jsonl 文件路径（>=2 份）")
    args = ap.parse_args()

    exam_dir = Path(args.exam_dir)
    bank = {json.loads(l)["task_id"]: json.loads(l)
            for l in (HERE / "bcb_hard.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}

    model_answers = {}
    for pat in args.answers:
        for f in sorted(glob.glob(str(Path(exam_dir) / pat) if not Path(pat).is_absolute() else pat)):
            name = Path(f).stem.replace("answers_", "")
            model_answers[name] = load_answers(Path(f))
    if len(model_answers) < 2:
        print("至少需要两份答案文件"); return 1

    task_ids = sorted(set().union(*[set(a) for a in model_answers.values()]))
    print(f"题目 {len(task_ids)} 道 × 模型 {list(model_answers)}")

    per, joint_ok, fail_joint = {}, [], []
    cache = (exam_dir / "moa_judge_cache.json")
    cached = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    for tid in task_ids:
        pb = bank.get(tid)
        if pb is None:
            continue
        results = {}
        for name, answers in model_answers.items():
            comp = answers.get(tid, "")
            if not comp.strip():
                results[name] = None
                continue
            key = f"{name}::{tid}"
            if key in cached:
                results[name] = cached[key]
            else:
                ok, _ = judge(pb, comp)
                results[name] = ok
                cached[key] = ok
        per[tid] = results
        if any(results.values()):
            joint_ok.append(tid)
        else:
            fail_joint.append(tid)
    cache.write_text(json.dumps(cached, ensure_ascii=False), encoding="utf-8")

    print("\n== 三级对照 ==")
    for name in model_answers:
        vals = [per[t][name] for t in per if per[t][name] is not None]
        if vals:
            print(f"单模型 {name}: {sum(vals)}/{len(vals)} = {sum(vals)/len(vals)*100:.0f}%")
    k = len(model_answers)
    print(f"MOA-pass@{k}: {len(joint_ok)}/{len(per)} = {len(joint_ok)/len(per)*100:.0f}%")
    (exam_dir / "moa_fails_for_arbiter.jsonl").write_text(
        "\n".join(json.dumps({"task_id": t}, ensure_ascii=False) for t in fail_joint), encoding="utf-8")
    print(f"双错待仲裁题: {len(fail_joint)} → 已写入 moa_fails_for_arbiter.jsonl（旗舰仲裁层加跑用）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
