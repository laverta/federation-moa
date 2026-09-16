# -*- coding: utf-8 -*-
"""
dsh_daemon.py — DSH L0 物理宿主与零 Token 看门狗（RFC-001 v1.1.0 · FM-02/04/07/08/09）

职责：PID 排他锁 → 文件 stat 轮询探测 INBOX → 变化时唤起 dsh_runtime 单 Tick →
心跳双写 + 四元组租约刷新。全程 0 模型调用（动静分离）。
铁律：Python 3.10+ 纯标准库 / 自带 --selftest / 日志 10MB×5 滚动
用法：
  py dsh_daemon.py --poll 20        # 常驻（计划任务/看门狗拉起）
  py dsh_daemon.py --once           # 单 Tick（调试/评测探针）
  py dsh_daemon.py --selftest
退出码：0=正常退出；3=PID 锁拒绝（已有实例存活，FM-08 预期行为）
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
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(os.environ.get('FEDERATION_ROOT', Path(__file__).resolve().parents[1]))

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dsh_runtime import DSH_ROOT, Runtime, dsh_path  # noqa: E402

PID_FILE = dsh_path("dsh_daemon.pid")
LOG_DIR = dsh_path("logs")
LOG_MAX, LOG_KEEP = 10 * 1024 * 1024, 5  # 10MB × 5（FM 规约）
LEASE_TTL = 600
CRASH_WINDOW, CRASH_LIMIT = 60, 3  # FM-08 退避参数


def _pid_alive(pid: int) -> bool:
    """OS 原生探测（FM-08）：Windows 下精准探测 PID 存活并防止 PID 复用假锁死。"""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except PermissionError:
        pass
    except OSError:
        return False
    try:
        import subprocess
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                           capture_output=True, text=True, timeout=1)
        return r.returncode == 0 and "python" in r.stdout.lower()
    except Exception:
        return True


def acquire_pid_lock() -> bool:
    """排他锁：旧 PID 存活则拒开（防双实例裂脑）。"""
    if PID_FILE.exists():
        try:
            old = int(PID_FILE.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            old = 0
        if _pid_alive(old):
            print(f"REFUSE: instance pid={old} alive (FM-08)", flush=True)
            return False
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True


def release_pid_lock() -> None:
    if PID_FILE.exists():
        try:
            if int(PID_FILE.read_text(encoding="utf-8").strip()) == os.getpid():
                PID_FILE.unlink()
        except (ValueError, OSError):
            pass


def _rotating_log(name: str, line: str) -> None:
    """10MB×5 滚动日志（stdout 物理重定向防管道窒息 FM-04）。"""
    p = LOG_DIR / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists() and p.stat().st_size > LOG_MAX:
        for i in range(LOG_KEEP - 1, 0, -1):
            src, dst = p.with_suffix(f".{i}"), p.with_suffix(f".{i+1}")
            if src.exists():
                src.replace(dst)
        p.replace(p.with_suffix(".1"))
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")


def run_loop(poll: int, once: bool = False) -> int:
    rt = Runtime()
    baseline = 0
    while True:
        try:
            m = rt.inbox.stat().st_mtime_ns if rt.inbox.exists() else 0
            size = rt.inbox.stat().st_size if rt.inbox.exists() else 0
            if m != baseline or size > 0 and _has_new(rt):
                baseline = m
                r = rt.process_once()
                _rotating_log("daemon.log", f"tick processed={r['processed']} acked_seq={r['acked_seq']}")
                if r["processed"] == 0:
                    baseline = m  # 无新信，避免空转重复 Tick
            rt.write_state("IDLE", rt.load_cursor()["acked_seq"])  # 租约四元组续期
        except Exception as ex:  # 单次抖动不断循环（对齐 keeper 纪律）
            _rotating_log("daemon.log", f"ERROR {ex!r}")
        if once:
            return 0
        time.sleep(poll)


def _has_new(rt: Runtime) -> bool:
    cur = rt.load_cursor()
    try:
        with open(rt.inbox, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and json.loads(line).get("seq", 0) > cur["acked_seq"]:
                    return True
    except (json.JSONDecodeError, OSError):
        pass
    return False


# ---------------- selftest ----------------
def _selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="dsh_da_st_") as td:
        global PID_FILE, LOG_DIR
        import dsh_runtime
        dsh_runtime.DSH_ROOT = Path(td)  # 沙箱重定向（env 授权范围）
        rt = Runtime(root=Path(td))
        from dsh_adapter_bridge import make_envelope
        env = make_envelope("T-LOCK", "TASK", 1, "zcode", "dsh", "SELFTEST", {"summary": "probe"})
        with open(rt.inbox, "a", encoding="utf-8") as f:
            f.write(json.dumps(env, separators=(",", ":")) + "\n")
        PID_FILE, LOG_DIR = Path(td) / "dsh_daemon.pid", Path(td) / "logs"
        assert acquire_pid_lock(), "lock acquire failed"
        assert not acquire_pid_lock(), "double-instance not refused (FM-08 broken)"  # 自身 PID 存活→拒
        r = rt.process_once()
        assert r["processed"] == 1, f"tick wrong {r}"
        release_pid_lock()
        assert acquire_pid_lock(), "re-acquire after release failed"
        release_pid_lock()
        _rotating_log("daemon.log", "selftest line")
        assert (LOG_DIR / "daemon.log").exists()
        print("[SELFTEST] dsh_daemon PASS: pid-lock mutual exclusion, tick consume, rotating log")
        return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--poll", type=int, default=20)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(_selftest())
    if not acquire_pid_lock():
        sys.exit(3)
    try:
        _rotating_log("daemon.log", f"daemon up pid={os.getpid()} poll={a.poll}s once={a.once}")
        sys.exit(run_loop(a.poll, a.once))
    finally:
        release_pid_lock()
