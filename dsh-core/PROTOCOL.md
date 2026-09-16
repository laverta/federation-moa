# DSH-CORE 宪法（PROTOCOL.md）

> 依据：DSH-CORE-RFC-001 v1.1.0（十二故障树立体防御 · 指挥官终裁 2026-09-06）
> 身份：DSH（新 DSH 联邦内核）· 核心实现=ZCode(OrangeCrane) · UI 图腾=反重力(WindyElk·Gemini) · 终裁=指挥官

## 一、身份与锚定

- 唯一物理根：`dsh-core/`（权威原点）。环境变量 `DSH_ROOT` **仅限测试沙箱重定向**，生产一律默认锚定。
- 全部内部寻址必须经 `dsh_path(rel)` 规范化（`os.path.normpath`），禁止裸相对路径（FM-03）。
- 含空格路径：跨进程一律列表传参或 `subprocess.list2cmdline`（FM-03/07）。

## 二、编码宪法（FM-07 · MUST）

- 所有文件 I/O 显式 `encoding="utf-8"`；
- 每个进程入口第一屏执行 `sys.stdout/stderr.reconfigure(encoding="utf-8")`（带 hasattr 防护）；
- subprocess 解码显式 utf-8 或 `errors="replace"`，禁裸 bytes。

## 三、信箱契约（FM-05/10 · MUST）

- 机器信箱：`INBOX.ndjson`（DSH 只读）/ `OUTBOX.ndjson`（DSH 只追加）——每行一个 canonical 信封 JSON；
- `.md` 文件仅是人类视窗投影，机器永不解析（FM-11 修正案）；
- **顺序契约（WAL）**：先落盘产出（OUTBOX 追加 + fsync）→ 后推移游标（cursor.json 原子替换）= At-least-once；
- **幂等去重**：复合键 `task_id#msg_type#seq`（ARCH v1.1），重复消费静默跳过；
- 原子写三步：`.tmp` → `flush+fsync` → `os.replace`。

## 四、存活契约（FM-08/09）

- 单实例：`dsh_daemon.pid` 排他锁，启动前 PID 存活探测，存活即拒开；
- 活性四元组：`state.json = {pid, mtime, lease_expires_at, last_seq}`——租约 TTL 600s，PID 在但租约超时 = 僵尸假死，强制回收；
- 看门狗递归终止于 Windows 计划任务（5min 自愈）；崩溃指数退避 30s→60s→120s→CRASH_DUMP.md 强制暂停；
- 心跳双写：`FED_ROOT\federation_bridge\HEARTBEATS\dsh.json`（I2 机制，总台席位点亮）。

## 五、资源契约（FM-06/12）

- 单工单步长配额 `MAX_CYCLE_STEPS=15`，同错 3 次触发 BLOCKED 熔断；
- 池级断路器：模型调用连续 2 次配额类报错 → 全局 TRIPPED → 降级 `DEGRADED_FILE_ONLY`（只转发文件与心跳，不唤醒模型）→ 桥上通报 → 等重置窗口自动复位。

## 六、调度契约（FM-02/04）

- 动静分离：L0 零 token 文件 stat 轮询；模型仅事件驱动单次唤醒；
- 外部执行：stdout 重定向日志文件 + 120s 硬超时，禁裸 `p.wait()`。

## 七、统一信封（不搞第二种）

所有公文遵循 federation_bridge_core 规范：canonical JSON（键排序紧凑序列化）+ SHA-256 16-hex checksum + 复合去重键。实现见 `dsh_adapter_bridge.py`。

## 八、变更纪律

本文件为宪法级固化文档，修改需两席会签 + 指挥官终裁。一切新机制登记 STATUS.md 台账。
