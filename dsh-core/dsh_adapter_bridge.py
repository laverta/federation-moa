# -*- coding: utf-8 -*-
"""
dsh_adapter_bridge.py — DSH L3 联邦信封适配器（RFC-001 v1.1.0 · 统一信封规约）

宪法：绝不造第二种信封——canonical JSON（键排序紧凑）+ SHA-256 16-hex + 复合去重键，
与 federation_bridge_core.py 规范完全对齐（该库为规范权威，本文件为 DSH 侧等价实现）。
铁律：Python 3.10+ 纯标准库 / 自带 --selftest
"""
from __future__ import annotations

import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # FM-07
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import hashlib
import json
import time


def canonical(payload: dict) -> str:
    """canonical 序列化：键排序 + 紧凑分隔（与核心库一致，跨端字节级可复现）。"""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def checksum16(payload: dict) -> str:
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()[:16]


def make_envelope(task_id: str, msg_type: str, seq: int, sender: str, recipient: str,
                  topic: str = "", payload: dict | None = None) -> dict:
    payload = payload or {}
    return {
        "task_id": task_id, "msg_type": msg_type, "seq": seq,
        "sender": sender, "recipient": recipient, "topic": topic,
        "created_at": round(time.time(), 3),
        "checksum": checksum16(payload),
        "payload": payload,
    }


def validate_envelope(env: dict) -> tuple[bool, str]:
    """校验：必填字段 + checksum 复算一致（坏信封旁路，不阻断队列）。"""
    for k in ("task_id", "msg_type", "seq", "sender", "recipient", "checksum", "payload"):
        if k not in env:
            return False, f"missing field {k}"
    if checksum16(env["payload"]) != env["checksum"]:
        return False, "checksum mismatch"
    return True, "ok"


def dedup_key(env: dict) -> str:
    """复合去重键 task_id#msg_type#seq（ARCH v1.1）。"""
    return f"{env.get('task_id','')}#{env.get('msg_type','')}#{env.get('seq')}"


# ---------------- selftest ----------------
def _selftest() -> int:
    env = make_envelope("DSH-TASK-001", "TASK", 7, "zcode", "dsh", "SELFTEST", {"summary": "统一信封"})
    ok, why = validate_envelope(env)
    assert ok, why
    assert canonical({"b": 1, "a": 2}) == '{"a":2,"b":1}', "canonical not sorted"
    bad = dict(env); bad["payload"] = {"summary": "被篡改"}
    ok2, why2 = validate_envelope(bad)
    assert not ok2 and "checksum" in why2, "tamper not detected"
    assert dedup_key(env) == "DSH-TASK-001#TASK#7"
    print("[SELFTEST] dsh_adapter_bridge PASS: canonical sorted, checksum verified, tamper rejected, dedup key ok")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(_selftest() if a.selftest else 0)
