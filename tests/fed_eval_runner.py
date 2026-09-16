# -*- coding: utf-8 -*-
"""
fed_eval_runner.py — 联邦 P2 评测运行器（Golden 测试 + 快照自动回滚）

分工（#76 确认生效）：ZCode=本运行器（沙盒子进程/断言/回滚）；反重力=golden 用例集（eval_golden\）+ 面板集成。
铁律：纯标准库 / 严格 D 盘 / 自带 --selftest（入库验货制三铁律）。

Golden 用例格式（*.json，一文件一案）:
{
  "id": "EVAL-001",
  "desc": "核心库自测",
  "cmd": "py ${FED_ROOT}/bridge/federation_bridge_core.py --selftest",
  "cwd": "${FED_ROOT}/bridge",
  "timeout_s": 60,
  "snapshot": ["${FED_ROOT}/master\\federation_bridge\\federation_bridge_core.py"],
  "assertions": [
    {"type": "exit0"},
    {"type": "contains", "value": "9/9 PASS"}
  ]
}
断言类型: exit0 / exitcode / contains / not_contains / regex / file_exists

用法:
  py fed_eval_runner.py                    # 跑 tests/eval_golden\\ 全部用例
  py fed_eval_runner.py --cases <dir>     # 指定用例目录
  py fed_eval_runner.py --selftest        # 自测（不入库先决条件）
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
import os
REPO_ROOT = Path(os.environ.get('FEDERATION_ROOT', Path(__file__).resolve().parents[1]))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

GOLDEN_DIR = Path(REPO_ROOT / "tests" / "eval_golden")
REPORT_PATH = REPO_ROOT / "tests" / "eval_report.json"
SNAP_ROOT = REPO_ROOT / "tests" / ".eval_snapshots"


def _check(a: dict, proc: subprocess.CompletedProcess, out: str) -> tuple[bool, str]:
    t = a.get("type")
    if t == "exit0":
        return proc.returncode == 0, f"exit={proc.returncode}"
    if t == "exitcode":
        ok = proc.returncode == int(a["value"])
        return ok, f"exit={proc.returncode} want={a['value']}"
    if t == "contains":
        return a["value"] in out, f"contains {a['value']!r}"
    if t == "not_contains":
        return a["value"] not in out, f"not_contains {a['value']!r}"
    if t == "regex":
        return re.search(a["value"], out) is not None, f"regex {a['value']!r}"
    if t == "file_exists":
        return Path(a["value"]).exists(), f"file_exists {a['value']}"
    return False, f"未知断言类型 {t!r}"


def _snapshot(paths: list[str], tag: str) -> dict[str, Path]:
    SNAP_ROOT.mkdir(parents=True, exist_ok=True)
    backup, mapping = SNAP_ROOT / tag, {}
    backup.mkdir(parents=True, exist_ok=True)
    for p in paths:
        src = Path(p)
        if src.exists():
            dst = backup / src.name
            shutil.copy2(src, dst)
            mapping[str(src)] = dst
    return mapping


def _rollback(mapping: dict[str, Path]) -> int:
    n = 0
    for src, dst in mapping.items():
        try:
            shutil.copy2(dst, src)
            n += 1
        except OSError:
            pass
    return n


def run_cases(case_dir: Path) -> dict:
    cases = sorted(case_dir.glob("*.json"))
    results, passed = [], 0
    for cf in cases:
        try:
            # utf-8-sig：容忍编辑器写入的 BOM 头（2026-09-08 case_12 曾因 BOM 静默解析失败）
            case = json.loads(cf.read_text(encoding="utf-8-sig"))
            # 展开 ${FED_ROOT} 占位符到全部路径类字段（cmd/cwd/snapshot/file_exists）
            def _exp(v):
                return v.replace("${FED_ROOT}", str(REPO_ROOT)) if isinstance(v, str) else v
            case["cmd"] = _exp(case.get("cmd", ""))
            case["cwd"] = _exp(case.get("cwd", "")) or None
            case["snapshot"] = [_exp(x) for x in case.get("snapshot", [])]
            for a in case.get("assertions", []):
                if a.get("type") == "file_exists":
                    a["value"] = _exp(a.get("value", ""))
        except Exception as ex:
            print(f"  [FAIL] {cf.name} — 用例解析失败: {ex}")
            results.append({"id": cf.name, "ok": False, "error": f"用例解析失败: {ex}"})
            continue
        tag = f"{case.get('id', cf.stem)}-{uuid.uuid4().hex[:6]}"
        snap = _snapshot(case.get("snapshot", []), tag)
        try:
            proc = subprocess.run(
                case.get("cmd", ""), cwd=case.get("cwd") or None, shell=True,
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=case.get("timeout_s", 60))
            out = (proc.stdout or "") + (proc.stderr or "")
            checks = [_check(a, proc, out) for a in case.get("assertions", [{"type": "exit0"}])]
            ok = all(c for c, _ in checks)
            detail = "; ".join(msg for _, msg in checks)
        except subprocess.TimeoutExpired:
            ok, detail, out = False, "超时", ""
        rolled = 0
        if not ok and snap:
            rolled = _rollback(snap)                 # 失败即回滚（P2 核心承诺）
        passed += ok
        results.append({"id": case.get("id", cf.stem), "ok": ok, "detail": detail,
                        "rolled_back_files": rolled, "at": time.strftime("%H:%M:%S")})
        print(f"  [{'PASS' if ok else 'FAIL'}] {case.get('id', cf.stem)} — {detail}"
              + (f"（已回滚 {rolled} 文件）" if rolled else ""))
    report = {"total": len(results), "passed": passed, "ts": time.time(), "results": results}
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.rmtree(SNAP_ROOT, ignore_errors=True)
    return report


def _selftest() -> int:
    box = Path(r"docs/lab\.eval_selftest")
    shutil.rmtree(box, ignore_errors=True)
    box.mkdir(parents=True)
    victim = box / "victim.txt"
    victim.write_text("BEFORE", encoding="utf-8")
    (box / "case_ok.json").write_text(json.dumps({
        "id": "ST-OK", "cmd": "py -c \"print('HELLO-EVAL')\"",
        "assertions": [{"type": "exit0"}, {"type": "contains", "value": "HELLO-EVAL"}]}),
        encoding="utf-8")
    (box / "case_rollback.json").write_text(json.dumps({
        "id": "ST-ROLLBACK", "cmd": f"py -c \"open(r'{victim}', 'w').write('AFTER')\"",
        "snapshot": [str(victim)],
        "assertions": [{"type": "exit0"}, {"type": "contains", "value": "绝不出现的字串"}]}),
        encoding="utf-8")
    report = run_cases(box)
    rolled_ok = victim.read_text(encoding="utf-8") == "BEFORE"      # 失败案回滚后应复原
    ok = report["passed"] == 1 and report["total"] == 2 and rolled_ok
    print(f"[SELFTEST] {'PASS' if ok else 'FAIL'}（含回滚验证）")
    shutil.rmtree(box, ignore_errors=True)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(GOLDEN_DIR))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    d = Path(args.cases)
    if not d.exists():
        print(f"用例目录不存在: {d}（反重力交付 eval_golden 后启用）")
        return 2
    report = run_cases(d)
    print(f"[EVAL] {report['passed']}/{report['total']} → {REPORT_PATH}")
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
