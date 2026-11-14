# 🌿 Federation-MOA

<div align="center">

### Lightweight Multi-Agent Sovereign Operating System & 3D World Tree Topology
**轻量级三剑客多智能体联邦操作系统与三维世界树总装系统**

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Pass@2](https://img.shields.io/badge/BCB--Hard-57.5%25%20Pass%402-emerald.svg)](docs/BENCHMARKS.md)
[![Pure StdLib](https://img.shields.io/badge/dependencies-Pure%20Standard%20Library-brightgreen.svg)](#quick-start)
[![World Tree 3D](https://img.shields.io/badge/visualizer-3D%20Three.js-purple.svg)](#3d-world-tree-visualizer)
[![Audit](https://img.shields.io/badge/security-Zero%20Leak%20Audit%20PASS-success.svg)](docs/RELEASE_AUDIT.md)

[English](#overview) | [中文说明](#项目概览) | [3D 世界树](#3d-world-tree-visualizer) | [评测战报](#benchmark-results) | [快速上手](#quick-start)

</div>

---

## 🌟 Overview / 项目概览

**Federation-MOA** is an open-source, sovereign multi-agent operating system designed to solve a fundamental challenge in modern AI engineering:

> **Can a collaborative workflow of ultra-lightweight, cost-efficient Flash models (DeepSeek v4.1 Flash, Gemini 3.8 Flash, GLM 5.3 Flash) outperform single-pass frontier monolithic models (such as GPT-5.6 / closed flagship APIs) on complex software engineering benchmarks?**

Through **3-Stage Forward DAG Compilation**, **Test-Time Compute (TTC) Token Expansion (~15,000 tokens/task)**, **T-1 Orthogonal Invariant Discrimination**, and an **Offline 3D World Tree Topology Engine**, Federation-MOA proves empirically that **architectural workflow beats brute-force parameter scaling**.

**Federation-MOA** 是一个开源的主权多智能体操作系统，旨在攻坚现代 AI 工程的核心命题：
> **能否仅依靠轻量级三剑客模型（DeepSeek v4.1 Flash、Gemini 3.8 Flash、GLM 5.3 Flash）的协同工作流，在复杂代码与系统工程基准测试中，彻底超越单体闭源旗舰大模型？**

本系统通过**前向 3 阶段 DAG 编译**、**测试时算力膨胀（TTC 时空换质量）**、**T-1 正交不变性鉴别器**以及**纯离线 3D 世界树拓扑感知**，以系统工程弥补了 Flash 模型长程注意力衰减的物理短板。

---

## 📊 Benchmark Results / 核心评测战报

Tested on the full 40-case **BigCodeBench-Hard (BCB-Hard)** dataset:

```
===================================================================================
 BigCodeBench-Hard (40-Problem Golden Test Suite)
-----------------------------------------------------------------------------------
 👑 Closed Frontier Monolith (Single Pass):           45.0%
 💎 Single Flash Model Solo (DeepSeek v4.1F):         45.0%
 💎 Single Flash Model Solo (Gemini 3.8F):            50.0%
 🌿 Federation-MOA (Pass@1, 3-Stage Workflow):        52.5%  (+7.5% vs Frontier)
 🚀 Federation-MOA (Pass@2, AST Self-Healing TTC):    57.5%  (+12.5% vs Frontier)
===================================================================================
```

- **Cost Efficiency**: Average token cost is less than **1/10th** of frontier API models.
- **Detailed Ledger**: See [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) for individual problem breakdowns and reproduction scripts.

---

## 🏛️ System Architecture / 架构拓扑

```
                           [ Commander Prompt / 宏观指令 ]
                                         │
                                         ▼
                 ┌────────────────────────────────────────────────┐
                 │ 💎 首席秘书长 (Gemini 3.8 Flash · 1M Context)   │
                 │   - 全景长文视界，意图宏观收敛                  │
                 │   - 编译为无状态的 DAG 任务切片 (<6K tokens/张) │
                 └───────────────────────┬────────────────────────┘
                                         │
                                         ▼
                 ┌────────────────────────────────────────────────┐
                 │ ⚔️ 军需装备官 (DeepSeek v4.1 Flash · T-1)       │
                 │   - 逆向冷酷挑刺，预判 3 大致命死穴            │
                 │   - 从 vault_index.json 精准配齐 1~3 件高星技能 │
                 └───────────────────────┬────────────────────────┘
                                         │
                                         ▼
                 ┌────────────────────────────────────────────────┐
                 │ 🔨 建造工程师 (GLM 5.3 Flash / Builder)         │
                 │   - 严格带装施工，本地 AST 语法解析            │
                 │   - 闭环自愈环路，消除 Flash 贪婪输出微瑕      │
                 └───────────────────────┬────────────────────────┘
                                         │
                                         ▼
                 ┌────────────────────────────────────────────────┐
                 │ 💎 结晶断面与 SHA-256 签名 (Sovereign Diff)     │
                 │   - Unified Diff 结晶，座舱 1-Click APPROVE   │
                 └────────────────────────────────────────────────┘
```

---

## 🌳 3D World Tree Visualizer / 三维世界树拓扑

Federation-MOA includes an offline-first **3D World Tree Topology Engine** (`cockpit/world_tree.html`) built with local Three.js & OrbitControls:
- **Central Energy Trunk**: Dynamic pulsing energy column representing core federation coordination;
- **Golden Z-Axis Data Cleansing Beam**: Vertical negative-entropy beam piercing all layers;
- **5 Subsystem Branch Tubes**:
  - West Branch (`ZCode High-Throughput Builder`)
  - East Branch (`Three Musketeers TTC Pipeline`)
  - North Branch (`Antigravity Architecture Explorer`)
  - South Branch (`Ergonomics & Visual UI Seat`)
  - Deep Root (`Deterministic AST Self-Healing Sandbox`)
- **Real-Time Dynamic Heartbeats**: Automatically connects to local seat heartbeats (`SilentBear`, `OrangeCrane`, `WindyElk`).

---

## 🚀 Quick Start / 快速上手

### 1. Zero-Dependency Cold Start (纯标准库一键冷启)

Federation-MOA core and visual cockpit require **ZERO third-party pip packages**. You only need standard Python 3.10+:

```bash
# Clone the repository
git clone https://github.com/laverta/federation-moa.git
cd federation-moa

# 1-Click Launch Cockpit & 3D World Tree (:8765)
python scripts/run_cockpit.py
```

Now open your browser:
- **Cockpit Dashboard**: [http://127.0.0.1:8765](http://127.0.0.1:8765)
- **3D World Tree**: [http://127.0.0.1:8765/world_tree](http://127.0.0.1:8765/world_tree)

### 2. Environment Configuration (可选 API 驱动)

Copy the `.env.example` template:

```bash
cp .env.example .env
```

Fill in your lightweight model keys:
```ini
DEEPSEEK_API_KEY=your_deepseek_key_here
GEMINI_API_KEY=your_gemini_key_here
GLM_API_KEY=your_glm_key_here
```

### 3. Run Benchmark Reproduction (复现 57.5% 评测战绩)

```bash
python -m bench.fed_eval_runner
```

### 4. Run Pre-Commit Leak Audit (安全脱敏合规门禁)

```bash
python scripts/leak_checker.py
```

---

## 📂 Repository Structure / 仓库目录说明

```
federation-moa/
├── README.md                    # 本文件 (中英双语全景说明)
├── LICENSE                      # Apache-2.0 开源协议
├── .env.example                 # 环境变量模板 (零物理 Key 保证)
├── requirements.txt             # 依赖声明 (核心链路纯标准库，额外特性可选)
│
├── dsh-core/                    # 【微内核无头运行时】
│   ├── runtime.py               # 联邦主权主机守护进程与状态机
│   ├── llm_adapter.py           # 统一轻量模型抽象层
│   └── dsh_advisor.py           # T-1 正交不变性鉴别器与红队外脑
│
├── moa-engine/                  # 【MOA 算力时空膨胀流水线】
│   ├── MOA_CHARTER.md           # 联邦多智能体协作宪法
│   ├── pipeline.py              # 3 阶段前向推理引擎
│   └── scheduler.py             # DAG 调度器与 yield_order 仲裁
│
├── cockpit/                     # 【人机工效与全景可视化座舱】
│   ├── server.py                # 纯标准库 HTTP / 备选 FastAPI 双引擎
│   ├── world_tree.html          # 3D 世界树拓扑渲染器 (WebGL)
│   └── static/                  # 本地静态库 (three.min.js, OrbitControls.js)
│
├── skills/                      # 【精选 6 件联邦技能宝库】
│   ├── vault_index.json         # 30 项本地高星技能元数据注册表
│   ├── moa/                     # 多智能体前向编排技能
│   ├── t-1/                     # T-1 元认知观测与范式打标技能
│   ├── federation-protocol/     # 联邦通信与心跳协议
│   ├── token-efficient/         # 极简高效 Token 上下文
│   ├── concise-mode/            # 高密度精简表达模式
│   └── data-cleansing/          # Z 轴数据清洗 (孵化中规范占位)
│
├── bench/                       # 【BCB-Hard 40 题全量基准测试套件】
│   ├── fed_eval_runner.py       # 评测复现主入口
│   └── bcb_hard_cases/          # 题目集与金样输入输出
│
├── tests/                       # 【单元与回归测试套件】
│   └── eval_golden/             # 12 案黄金系统回归套件
│
├── docs/                        # 【架构典籍与白皮书】
│   ├── DSH_ARCHITECTURE_CHRONICLES.md # 联邦四代架构全景编年史
│   ├── BENCHMARKS.md            # 40 题评测全量战台白皮书
│   └── RELEASE_AUDIT.md         # 开源总装终审合规报告
│
└── scripts/                     # 【工程快捷方式与质量门禁】
    ├── run_cockpit.py           # 一键启动座舱与世界树
    └── leak_checker.py          # 零泄漏合规扫描器 (Pre-Commit 门禁)
```

---

## 📜 Chronicles of Evolution / 联邦四代演进编年史

Federation-MOA is the culmination of four iterative evolutionary eras:
1. **Case 01 (`DSH-V1-SPATIAL`)**: 2.5D Cyber Guild Town, Sprite snoring state machine, metabolism pruning;
2. **Case 02 (`DSH-V2-SOVEREIGN-MOA`)**: Dual-rail thinking cockpit (:8765), 1M context convergence, SHA-256 crystal diffs;
3. **Case 03 (`DSH-V3-NORTH-STAR`)**: Polar anchor constitution, out-of-band T-1 red-team advisor;
4. **Case 04 (`DSH-V4-THREE-MUSKETEERS`)**: Lightweight three musketeers, Test-Time Compute expansion, 3D World Tree.

Full architectural accounts can be found in [`docs/DSH_ARCHITECTURE_CHRONICLES.md`](docs/DSH_ARCHITECTURE_CHRONICLES.md).

---

## 🤝 Contribution & Governance / 贡献与治理

We welcome contributions from the community! Please ensure:
1. Run `python scripts/leak_checker.py` before submitting any pull requests (must exit 0);
2. Respect the pure standard library principle for core runtime dependencies;
3. Adhere to the T-1 neutral observation principles defined in `skills/t-1/`.

---

## 📄 License

Federation-MOA is licensed under the [Apache-2.0 License](LICENSE).

---

<!-- LAVERTA-FEDERATION-ECOSYSTEM-LINK -->
## 🔗 Laverta Federation Ecosystem / 联邦生态关联

**`federation-moa`** is the execution & orchestration core of the **[Laverta Federation Ecosystem](https://github.com/laverta)**. It unifies the DSH evolutionary lineage (`DSH-V1` → `DSH-V4`) with:
- **[`dsh-skill-registry`](https://github.com/laverta/dsh-skill-registry)**: Task-gated on-demand skill mounting & boundary governance (`dsh-core`, `skills/vault_index.json`).
- **[`t-1`](https://github.com/laverta/t-1)** (evolved from **[`mindharp`](https://github.com/laverta/mindharp)**): Neutral third-person & orthogonal invariant discrimination (`dsh-core/dsh_advisor.py`, `skills/t-1/`).
- **[`federation-communication-lite`](https://github.com/laverta/federation-communication-lite)**: Bounded cross-session message contract (`skills/federation-protocol/`).
- **[`zcode-gemini-bridge`](https://github.com/laverta/zcode-gemini-bridge)**: Local `thought_signature` proxy enabling Gemini thinking models in ZCode builder seats.

| Layer | Repository | Role & Cross-Repo Connection |
|---|---|---|
| **Profile Hub** | [laverta/laverta](https://github.com/laverta) | Master architecture map, genealogy & ecosystem index |
| **Core OS & Orchestration** | [laverta/federation-moa](https://github.com/laverta/federation-moa) | 3-Stage DAG multi-agent OS & 3D World Tree (57.5% vs 45% BigCodeBench-Hard); integrates `dsh-core`, `t-1`, and federation protocols |
| **Task Router & Governance** | [laverta/dsh-skill-registry](https://github.com/laverta/dsh-skill-registry) | DSH task router & skill registry; on-demand 1–3 skill mounting & privilege guard against context bloat |
| **Inter-Agent Protocol** | [laverta/federation-communication-lite](https://github.com/laverta/federation-communication-lite) | Platform-neutral agent delivery layer (`Native messaging > Shared Markdown > Bridge`), companion to `federation-moa` |
| **Metacognitive Observer** | [laverta/t-1](https://github.com/laverta/t-1) | Third-One (`观测端·镜子`): neutral paradigm tagging & orthogonal invariant discrimination embedded in `federation-moa`; evolved from `mindharp` |
| **Cognitive Restructuring** | [laverta/r-1](https://github.com/laverta/r-1) | Rewire-One (`落地端·刻刀`): ADHD/AuDHD self-understanding & rewiring; symmetric counterpart to `t-1`, evolved from `mindharp` |
| **Origin / Predecessor** | [laverta/mindharp](https://github.com/laverta/mindharp) | Origin cognitive-mechanics framework (2026-08) that evolved into `t-1` and `r-1` |
| **Model Bridge Infra** | [laverta/zcode-gemini-bridge](https://github.com/laverta/zcode-gemini-bridge) | Local proxy fixing Gemini 3.x `thought_signature` 400 errors for ZCode & multi-agent harnesses |

> **Canonical Ecosystem Hub**: [`https://github.com/laverta`](https://github.com/laverta) · See [`CITATION.cff`](CITATION.cff) for machine-readable cross-repository citations.
