---
name: token-efficient
description: 治理 Agent 自动化长程循环中的 Token 浪费与输出拖沓。包含禁止套话、禁止重复读盘、强制局部 Diff 替换、严禁全文件覆写等 9 大黄金守则。适用场景：跨窗口协作 / 公文长线程 / 大规模代码重构 / 自动化流水线。
author: WindyElk (反重力席 · 吸收自 drona23/claude-token-efficient)
version: 1.0.0
rating: ★★★
inputs: [工程任务, 代码修改, 跨席公文]
outputs: [高密度Diff, 零废话回复, 紧凑公文]
tags: [token-efficiency, prompt-engineering, engineering-standards, optimization]
---
# Token 高效工程规约（token-efficient）

> 来源：吸收自 GitHub 开源标杆 drona23/claude-token-efficient，已完成联邦标准 D: 盘本土化适配。
> 目的：在长程多 Agent 协同与复杂工程交付中，削减 50% ~ 75% 的无效输出 Token 损耗。

## 一、九大反浪费铁律
1. **三无原则**：零寒暄、零客套、零机械复述背景，首句直奔主题；
2. **禁止整文件重写**：修改代码必须使用精确的行块替换（Replace Chunk / Diff），严禁覆写整个大文件；
3. **禁止重复读盘**：上下文已包含的文件严禁二次发起读取；
4. **深度思考，极简动作**：思维链穷尽推演，但对外公文只输出结论与可执行动作；
5. **结论先行**：采用【核心结论】➔【论据数据】➔【行动清单】三段式结构；
6. **本地测试闭环**：代码改动必须先跑回归探针验证，确认绿码后再报告结果；
7. **坚守 YAGNI**：只写当前工单必须的逻辑，不凭空前置抽象；
8. **错误直接暴露**：遇阻直接给出调用栈与错误码，不含糊、不掩饰；
9. **指令最高裁决**：指挥官针对输出格式的指令动态覆盖本守则。
