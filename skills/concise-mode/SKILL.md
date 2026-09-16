---
name: concise-mode
description: 中文环境高密度精简表达协议。通过表达层（剔除冗余修饰）与内容层（核心结论+要点列表）双层压缩，根治大语言模型在中文 CJK 语境下的 Token 快速膨胀问题。提供 Standard、Lite、Ultra 三档压缩强度。
author: WindyElk (反重力席 · 吸收自 Cpp1022/concise)
version: 1.0.0
rating: ★★★
inputs: [自然语言汇报, 审计通报, 跨席合议公文]
outputs: [高密度中文公文, 结构化简报]
tags: [concise, chinese-compression, communication-protocol, high-density]
---
# 中文高密度极简模式（concise-mode）

> 来源：吸收自 GitHub 开源项目 Cpp1022/concise，适配联邦公文与终端交互。
> 解决痛点：中文 CJK 字符在主流大模型 Tokenizer 中切分粒度细、单字 Token 成本高。传统 LLM 繁琐的铺垫和排比句式导致会话上下文迅速劣化。

## 一、双层压缩算法
1. **表达层压缩**：剔除口癖与垫话（'综上所述'、'显而易见'）、剔除防御性前缀（'作为AI'）、剔除从句包裹；
2. **内容层压缩**：首句直接输出判断或产物（BLUF），纯文字分析控制在三段以内，优先采用表格与键值对。

## 二、三档压缩模式
- **Standard（默认）**：方案评审、综合复盘。结构严整，结论先行，保留核心论据与文件名；
- **Lite（轻量工作流）**：每日站会、状态轮询。只报【状态 + 任务 + 下一步】，不超过 5 行；
- **Ultra（自动化链路）**：守护进程回执、探针。只输出单行纯键值对。
