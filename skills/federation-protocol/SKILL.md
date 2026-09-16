---
name: federation-protocol
description: 联邦协作纪律（v1.2.x 协议族 + 七列表 + 会话纪律）。任何新 agent/会话加入联邦或多 agent 协作时使用：上岗流程、发信格式、线程纪律、退出交接。Trigger：联邦 / 上桥 / 接入 / 发信给其他 agent / STATUS.md / 立项 / 交付验收 / 工作模式。
author: ZCode (OrangeCrane · GLM-5.3)
version: 1.0.0
rating: ★★★
inputs: [任务指派, 邮件桥访问]
outputs: [合规公文, 台账更新]
tags: [federation, protocol, onboarding, governance]
---

# 联邦协作纪律（federation-protocol）

> 装上本技能 = 拿到联邦上岗资格。一切细节以 `docs/STATUS.md`（现状）为准，本技能是操作规程。

## 一、上岗四步（任何新会话/新席位）

1. 读 `docs/STATUS.md`（唯一现状简报，**不读历史过程**）；
2. 确认自己的邮箱身份与 token（`am_agent_tokens.json`；独立身份，**严禁冒用他席**）；
3. 发报到信：主题 `[FED-COORD] <名字> 上岗报到`，topic 填 `FED-COORD`，一句话职责声明；
4. 写心跳：`HEARTBEATS\<agent>.json`（独占写；字段 agent/ts/status/task/mode）。

## 二、发信纪律（协议 v1.2 / v1.2.1 / v1.2.2）

- 任务信：主题 `[TASK-ID] 前缀` + `topic=TASK-ID` + 回信用 reply 保持线程；**多任务绝不共用线程**；
- 立项信：开工即发 `[TASK-ID] OPEN:`（一句即可，注明执行者+范围）；交付与状态变化同线程流转；
- **署名块**（正文末尾，必带）：署名（作者）/ 目标（收件席位）/ 分工（执行·咨询·验收·仲裁）；
- 口头指派：正文注明 `requested_by: human in <agent> window`；
- 铁律③：指挥官窗口指令 > 桥上一切排队状态；桥是台账，人是权威。

## 三、工作循环

- 工作模式口令：「开始工作/长时间工作」进入（写 WORKMODE.json，4h 租约，每 120s 刷 mtime），「结束工作」退出；
- 值守：例程零 token（keeper/值影代行），行动级信才唤醒模型；
- 凡机制必填七列表：触发/检测/动作/预算/超时/失败模式/回滚——填不齐的不是机制，是小说；
- 上下文将满：不慌，台账即记忆——提醒指挥官"新窗口说『开始工作』直接接棒"。

## 四、红线

不写 C 盘（读除外）；不改桥核心脚本（走立项）；不冒用他席身份；需终裁的事不拍板、上呈。

## 参考

- `references/checklist.md` — 发信前 30 秒自检清单
- `docs/FEDERATION_ENGINEERING_FRAMEWORK.md` — 工程总框架
- `docs/FED_ZCODE_MECHANICS.md` — ZCode 会话机制底图
