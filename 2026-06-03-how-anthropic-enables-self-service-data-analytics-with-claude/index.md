---
title: "How Anthropic enables self-service data analytics with Claude"
title_zh: "Anthropic 如何用 Claude 实现自助式数据分析"
author: "Chen Chang, Clement Peng, Justin Leder, Johanne Jiao, Josh Cherry"
source: "https://claude.com/blog/how-anthropic-enables-self-service-data-analytics-with-claude"
published: "2026-06-03"
recorded: "2026-06-06"
tags:
  - daily-reading
  - anthropic
  - claude
  - claude-code
  - data-analytics
  - self-service-analytics
  - data-engineering
  - skills
  - evaluations
---

# How Anthropic enables self-service data analytics with Claude / Anthropic 如何用 Claude 实现自助式数据分析

这是一篇每日阅读记录，已拆分为多个文件，便于分别阅读、修改和补充笔记。

## 文件

- [中文详细译述](translation.zh.md)
- [英文来源结构图](original.en.md)
- [元信息](meta.json)
- [阅读笔记](notes.md)

## 来源

- 原文链接：https://claude.com/blog/how-anthropic-enables-self-service-data-analytics-with-claude
- 作者：Chen Chang, Clement Peng, Justin Leder, Johanne Jiao, Josh Cherry
- 发布日期：2026-06-03
- 记录日期：2026-06-06

## 摘要

文章讨论 Anthropic 如何把 Claude 用于企业内部自助式业务分析。核心结论是：分析准确率主要不是 SQL 代码生成问题，而是上下文、数据定义、检索路径和验证机制的问题。

Anthropic 将多数错误归因于三类模式：业务概念无法稳定映射到正确的数据实体，数据源和业务定义随时间变旧，以及 agent 没能找到已经存在的正确上下文。为此，他们构建了由数据基础、可信来源、Skills 和验证体系组成的 agentic analytics stack。

文章最有价值的部分是工程化细节：语义层必须优先于手写 SQL，参考文档要按 LLM 可检索方式编写，Skills 要与数据模型共仓维护，eval 结果要像 telemetry 一样入仓，线上答案要带 provenance footer。它给出的启发是，面向分析的 agent 不是“让模型自由查数”，而是把资深分析师的判断路径产品化、版本化和可回归验证。
