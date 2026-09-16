# moa 参考库：基准工具与锚点来源

## 自有工具（联邦资产，纯标准库）
- `bench\llm_bench.py` — 直连双模型 harness（HumanEval pass@1，断点续跑）
- `bench\dsh_bench.py` — DSH 工单通道评测（信封投递→daemon→回执→判定）
- `bench\results_*.jsonl` — 逐题原始数据（可复核）

## 外部框架（隔离 venv 临时使用，不入库核心）
| 基准 | 仓库 | 用法要点 | 状态 |
|---|---|---|---|
| BigCodeBench-Hard | github.com/bigcode-project/bigcodebench | `pip install bigcodebench`；OpenAI 兼容 `--base_url` 接 DeepSeek；免 Docker=E2B 远程沙箱或本地隔离环境 | 仓库归档但稳定，首选进阶基准 |
| LiveCodeBench | github.com/livecodebench/livecodebench | 官方 CLI，OpenAI 兼容 API，题库持续更新免污染 | 备选 |
| IFEval（指令遵循） | github.com/oKatanaaa/ifeval | 轻量 Python API+CLI，秘书/公文岗专用 | 备选 |
| EvalScope | github.com/modelscope/evalscope | 一站式多基准，依赖较重 | 谨慎使用 |
| Terminal-Bench | tbench.ai / harbor-framework | 需 Docker+Harbor | 无 Docker 暂跳过 |

## 锚点分数来源（引用时注明不确定性）
- Terminal-Bench 3.0：GPT-5.6 Sol(max)/Codex = 34.6% ± 3.1%（tbench.ai 官方榜；第三方 benchlm.ai 快照有出入，以官方为准）
- BigCodeBench-Hard：GPT-5.6 Sol = 42.6%、Claude Opus 4.8 = 44.1%（第三方系统卡/评测汇总，注意版本时效）
- HumanEval 饱和带：前沿 12 模型 >95%；GPT-5.5 = 94.2%（onyx.app 汇总）
- 价格：OpenRouter（GLM-5.3-Flash $0.075/$0.25）、Google 官方（3.8 Flash 促销 $0.75/$3.75 至 2026-12-31）、DeepSeek 峰谷制
- GLM-5.3-Flash 规格：1.31M 上下文、AA 智能指数 57、DeepSWE v1 63.4（Z.ai 官方博客）

## 诚实边界备忘
1. HumanEval 已饱和——flash 模型高分 ≠ 旗舰同等 agentic 能力；
2. 第三方榜单分数常因 harness/采样参数不同而有 ±3-5% 出入，本联邦结论以自测为准；
3. 机房代理 IP 可能触发 Gemini 地域 400（FAILED_PRECONDITION），测前先验出口。
