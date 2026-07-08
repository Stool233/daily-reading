---
title: "Harness Engineering for Self-Improvement"
title_zh: "用于自我改进的 Harness 工程"
author: "Lilian Weng"
source: "https://lilianweng.github.io/posts/2026-07-04-harness/"
published: "2026-07-04"
recorded: "2026-07-09"
tags:
  - daily-reading
  - ai-agents
  - harness-engineering
  - self-improvement
  - context-engineering
  - auto-research
  - evolutionary-search
  - agent-runtime
---

# Harness Engineering for Self-Improvement / 用于自我改进的 Harness 工程

这是一篇每日阅读记录，已拆分为多个文件，便于分别阅读、修改和补充笔记。

## 文件

- [中文详细译述](translation.zh.md)
- [英文来源结构图](original.en.md)
- [元信息](meta.json)
- [阅读笔记](notes.md)

## 来源

- 原文链接：https://lilianweng.github.io/posts/2026-07-04-harness/
- 作者：Lilian Weng
- 发布日期：2026-07-04
- 记录日期：2026-07-09
- 对应 issue：https://github.com/Stool233/daily-reading/issues/7

## 摘要

Lilian Weng 将 AI 自我改进的近期路径从“模型直接改写自身权重”转向更工程化的层面：模型之外的 harness，也就是围绕基础模型的运行系统。Harness 负责工作流、工具调用、上下文管理、持久状态、权限、评估和结果验证，因此它本身也会成为可优化对象。

文章把 harness 工程拆成几个层次：设计模式包括工作流自动化、文件系统作为持久记忆、子 agent 与后台任务；优化对象则从 prompt、结构化上下文、workflow、harness code，一路走向 optimizer code。相关研究包括 ACE、MCE、Meta-Harness、AI Scientist、ScientistOne、ADAS、AFlow、STOP、Self-Harness、Promptbreeder、GEPA、AlphaEvolve 等。

文章的谨慎点也很重要：自我改进循环依赖评估器、权限边界、长期质量信号和人类监督。一旦优化目标模糊、反馈偏短期、失败经验没有被保存，harness 的自我优化很容易过拟合 benchmark、奖励模型或局部测试，而不是提高真实系统能力。
