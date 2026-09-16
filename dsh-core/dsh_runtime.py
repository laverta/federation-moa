# -*- coding: utf-8 -*-
"""
dsh_runtime.py — DSH L1 神经状态机与单写原子队列（RFC-001 v1.1.0 · FM-03/05/07/10）

铁律：Python 3.10+ 纯标准库 / 严格 D 盘自闭环 / 自带 --selftest（入库验货制）
顺序契约：先落盘产出(OUTBOX+fsync) → 后推游标(cursor 原子替换) = At-least-once
幂等去重：复合键 task_id#msg_type#seq（ARCH v1.1）
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
import os
REPO_ROOT = Path(os.environ.get('FEDERATION_ROOT', Path(__file__).resolve().parents[1]))

DSH_ROOT = Path(os.environ.get("DSH_ROOT", str(Path(__file__).resolve().parent)))  # 锚定=dsh-core 目录，env 仅测试(FM-03)
STATES = ["IDLE", "SENSING", "PLANNING", "EXECUTING", "REPORTING"]
LEASE_TTL = 600  # FM-09
MAX_CYCLE_STEPS = 15  # FM-06
HEARTBEAT_FILE = Path(r"FED_ROOT\federation_bridge\HEARTBEATS\dsh.json")  # I2 双写


def dsh_path(rel: str) -> Path:
    """宪法寻址：唯一规范绝对路径入口，禁裸相对寻址（FM-03）。"""
    return (DSH_ROOT / rel).resolve() if os.path.isabs(rel) is False else Path(os.path.normpath(rel))


def atomic_write(path: Path, text: str) -> None:
    """原子写三步：.tmp → flush+fsync → os.replace（FM-05）。显式 UTF-8（FM-07）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


class Runtime:
    """L1 状态机 + 信箱 + WAL 游标。单写者：每 DSH 实例独占自己的 OUTBOX/cursor。"""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else DSH_ROOT
        self.inbox = self.root / "INBOX.ndjson"
        self.outbox = self.root / "OUTBOX.ndjson"
        self.cursor_file = self.root / "cursor.json"
        self.state_file = self.root / "state.json"
        self.state_md = self.root / "STATE.md"
        for f in (self.inbox, self.outbox):
            f.parent.mkdir(parents=True, exist_ok=True)
            f.touch(exist_ok=True)

    # ---------- cursor / WAL (FM-10) ----------
    def load_cursor(self) -> dict:
        if self.cursor_file.exists():
            with open(self.cursor_file, encoding="utf-8") as f:
                return json.load(f)
        return {"acked_seq": 0, "committed_keys": [], "seq_version": 0}

    def _save_cursor(self, cur: dict) -> None:
        cur["seq_version"] = cur.get("seq_version", 0) + 1  # 版本序列号先落盘后使用
        atomic_write(self.cursor_file, json.dumps(cur, ensure_ascii=False, indent=1))

    # ---------- 状态四元组 (FM-09) ----------
    def write_state(self, status: str, last_seq: int, extra: dict | None = None) -> None:
        now = time.time()
        st = {
            "agent": "dsh",
            "pid": os.getpid(),
            "mtime": now,
            "lease_expires_at": now + LEASE_TTL,
            "last_seq": last_seq,
            "status": status,
            "mode": "resident",
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if extra:
            st.update(extra)
        atomic_write(self.state_file, json.dumps(st, ensure_ascii=False, indent=1))
        atomic_write(self.state_md,
                     f"# DSH 运行态（投影 · 机器勿读）\n\n- status: **{status}**\n- last_seq: {last_seq}\n"
                     f"- lease_expires_at: {int(st['lease_expires_at'])}\n- pid: {os.getpid()}\n"
                     f"- 更新: {st['ts']}\n")
        try:  # 心跳双写（I2）：桥侧注册表，失败不阻断主流程
            hb = {"agent": "dsh", "ts": st["ts"], "status": status, "task": "DSH-CORE", "mode": "resident"}
            HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(HEARTBEAT_FILE, json.dumps(hb, ensure_ascii=False, indent=1))
        except OSError:
            pass

    # ---------- 信箱 ----------
    def _read_new_envelopes(self, cur: dict) -> list[dict]:
        """增量读：只取 seq > acked_seq 且未提交复合键的行（幂等去重 FM-10）。"""
        committed = set(cur["committed_keys"])
        out, seen_seq = [], cur["acked_seq"]
        with open(self.inbox, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    env = json.loads(line)
                except json.JSONDecodeError:
                    continue  # 坏行旁路（毒丸隔离，对齐核心库语义）
                seq = int(env.get("seq", 0))
                key = f"{env.get('task_id','')}#{env.get('msg_type','')}#{seq}"
                if seq <= cur["acked_seq"] or key in committed:
                    continue
                out.append(env)
                seen_seq = max(seen_seq, seq)
        return out

    @staticmethod
    def _append_outbox(path: Path, env: dict) -> None:
        """产出先行：追加 + fsync（顺序契约第一步）。"""
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(env, ensure_ascii=False, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def process_once(self, handler=None) -> dict:
        """一个离散 Tick：SENSING→PLANNING→EXECUTING→REPORTING→IDLE。"""
        self.write_state("SENSING", self.load_cursor()["acked_seq"])
        cur = self.load_cursor()
        news = self._read_new_envelopes(cur)
        results = []
        for env in news:
            self.write_state("EXECUTING", cur["acked_seq"], {"task": env.get("task_id", "")})
            receipt = handler(env) if handler else self._default_handler(env)
            self._append_outbox(self.outbox, receipt)  # ① 先落盘产出
            key = f"{env.get('task_id','')}#{env.get('msg_type','')}#{env.get('seq')}"
            cur["committed_keys"] = (cur["committed_keys"] + [key])[-500:]  # 有界账本
            cur["acked_seq"] = max(cur["acked_seq"], int(env.get("seq", 0)))
            results.append(key)
        self._save_cursor(cur)  # ② 后推游标（WAL 顺序契约第二步）
        self.write_state("IDLE", cur["acked_seq"])
        return {"processed": len(results), "keys": results, "acked_seq": cur["acked_seq"]}

    @staticmethod
    def _default_handler(env: dict) -> dict:
        """L2 执行器：DeepSeek 推理（Phase 4）；熔断/失败降级为骨架 ACK 回执（DEGRADED_FILE_ONLY 语义）。"""
        from dsh_adapter_bridge import make_envelope
        prompt = env.get("payload", {}).get("summary", "")
        answer, status = None, "RESULT"
        try:
            from dsh_llm import chat
            answer = chat(f"[联邦工单 {env.get('task_id','')}] {prompt}")
        except Exception as ex:  # FM-12：降级不阻断，工单照常回执
            answer, status = f"DEGRADED_FILE_ONLY: LLM 不可用（{ex}），已按文件模式回执", "DEGRADED"
        return make_envelope(
            task_id=env.get("task_id", "UNKNOWN"), msg_type=status,
            seq=int(env.get("seq", 0)), sender="dsh", recipient=env.get("sender", "zcode"),
            topic=env.get("topic", ""),
            payload={"summary": prompt[:120], "answer": answer, "executed_by": "dsh_llm" if status == "RESULT" else "skeleton"},
        )


# ---------------- selftest（入库验货制） ----------------
def _selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="dsh_st_") as td:  # 测试沙箱：env 重定向授权范围
        rt = Runtime(root=Path(td))
        from dsh_adapter_bridge import make_envelope
        envs = [make_envelope(task_id=f"T{i}", msg_type="TASK", seq=i + 1, sender="zcode",
                              recipient="dsh", topic="SELFTEST", payload={"summary": f"case {i}"})
                for i in range(3)]
        with open(rt.inbox, "a", encoding="utf-8") as f:
            f.writelines(json.dumps(e, ensure_ascii=False, separators=(",", ":")) + "\n" for e in envs)
        r1 = rt.process_once()
        assert r1["processed"] == 3 and r1["acked_seq"] == 3, f"first tick wrong: {r1}"
        with open(rt.outbox, encoding="utf-8") as f:
            n_receipts = sum(1 for _ in f)
        assert n_receipts == 3, f"outbox receipts {n_receipts} != 3"
        r2 = rt.process_once()  # 幂等：重复 Tick 零副作用
        assert r2["processed"] == 0, f"idempotency broken: {r2}"
        with open(rt.outbox, encoding="utf-8") as f:
            assert sum(1 for _ in f) == 3, "outbox grew on idle tick"
        st = json.loads(rt.state_file.read_text(encoding="utf-8"))
        assert all(k in st for k in ("pid", "mtime", "lease_expires_at", "last_seq")), "quad missing"
        print("[SELFTEST] dsh_runtime PASS: 3 consumed, 3 receipts, idempotent re-tick, quad-lease ok")
        return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(_selftest() if a.selftest else 0)
