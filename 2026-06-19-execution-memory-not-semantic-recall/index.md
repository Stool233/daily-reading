---
title: "Execution Memory，而不是 Semantic Recall"
title_zh: "执行记忆，而不是语义召回"
author: "tommy0103"
source: "https://tommy0103.github.io/project_silica/"
published: "2026-06"
recorded: "2026-06-19"
tags:
  - daily-reading
  - ai-agents
  - coding-agents
  - memory
  - retrieval
  - obelisk
---

# Execution Memory，而不是 Semantic Recall / 执行记忆，而不是语义召回

这是一篇每日阅读记录。原文为中文，因此本归档保存来源结构图、中文详细读书稿、元信息和阅读笔记，而不重复转载全文。

## 文件

- [中文详细读书稿](translation.zh.md)
- [中文来源结构图](original.zh.md)
- [元信息](meta.json)
- [阅读笔记](notes.md)

## 来源

- 原文链接：https://tommy0103.github.io/project_silica/
- 作者：tommy0103
- 发布日期：2026-06
- 记录日期：2026-06-19

## 摘要

文章围绕 Obelisk 展开，核心判断是 coding-agent session 不是普通聊天记录，而是一种可查询、可审计、可复现的 execution memory。作者认为，向量检索和语义召回并不应该默认定义所有 agent memory 问题；对 coding agent history 来说，很多问题更适合用明确检索、结构化索引和可展开证据链解决。

文章从递归 agent 结构、dynamic workflow 的中间上下文问题写起，解释为什么 CodeAct/JavaScript 查询比 URI/DSL/多轮 CLI 调用更适合作为检索语言。随后讨论 Obelisk 从 raw SQL 走向 helper function 和渐进披露的过程，以及 SkillOpt 暴露出的 overfetch 问题。

最后，作者把 Obelisk 能工作的原因归结为 coding agent session 的特殊性：任务中心、主干明确、有工具调用和文件路径等外部锚点，并且跨 session 存在项目、分支、时间线和 memory 等自然结构。
