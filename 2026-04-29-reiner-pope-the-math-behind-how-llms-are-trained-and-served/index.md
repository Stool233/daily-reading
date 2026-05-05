---
title: "Reiner Pope - The math behind how LLMs are trained and served"
title_zh: "Reiner Pope：LLM 训练与服务背后的数学"
author: "Dwarkesh Patel"
source: "https://www.youtube.com/watch?v=xmkSf5IS-zw"
published: "2026-04-29"
recorded: "2026-05-05"
tags:
  - daily-reading
  - ai-infrastructure
  - llm
  - inference
  - training
  - gpu
  - moe
---

# Reiner Pope - The math behind how LLMs are trained and served / Reiner Pope：LLM 训练与服务背后的数学

这是一篇每日阅读记录，已拆分为多个文件，便于分别阅读、修改和补充笔记。

## 文件

- [中文完整译文](translation.zh.md)
- [英文文稿](original.en.md)
- [英文练习卡片](flashcards.en.md)
- [中文练习卡片](flashcards.zh.md)
- [本地图片资源](assets/images/)
- [元信息](meta.json)
- [阅读笔记](notes.md)

## 来源

- YouTube：https://www.youtube.com/watch?v=xmkSf5IS-zw
- 官方发布页：https://www.dwarkesh.com/p/reiner-pope
- 文稿来源：https://gist.githubusercontent.com/dwarkeshsp/79100f0fdeed69d76241903bb0604dbe/raw/b5810c077e8ca37fe7dfd917f75a883b4c6ff688/reiner-dwarkesh-transcript.md
- 相关 flashcards：https://reiner-flashcards.vercel.app/
- 主持人：Dwarkesh Patel
- 嘉宾：Reiner Pope
- 发布日期：2026-04-29
- 记录日期：2026-05-05

## 摘要

这期访谈是一场关于 LLM 训练和推理系统的黑板课，核心是用 roofline analysis 把模型架构、硬件带宽、FLOPs、batch size、KV cache 和 API 价格联系起来。Reiner Pope 解释了为什么批处理能显著降低每 token 成本，但对延迟存在由 HBM 带宽和模型权重读取决定的下界。

访谈还讨论了 MoE 模型如何映射到 GPU rack、pipeline parallelism 为什么在训练和架构演进中带来约束，以及为什么 RL 和大规模推理需求可能让前沿模型远远超过 Chinchilla-optimal 的预训练 token 数。后半部分用长上下文 API 定价反推出 KV cache 成本，并把神经网络与密码学的多层混合结构作了一个类比。
