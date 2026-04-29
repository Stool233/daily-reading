---
title: "Illegal vs Unwanted States"
title_zh: "非法状态 vs 不想要的状态"
author: "Hillel Wayne"
source: "https://buttondown.com/hillelwayne/archive/illegal-vs-unwanted-states/"
published: "2026-04-28"
recorded: "2026-04-30"
tags:
  - daily-reading
  - software-design
  - formal-methods
---

# Illegal vs Unwanted States / 非法状态 vs 不想要的状态

这是一篇每日阅读记录，已拆分为多个文件，便于分别阅读、修改和补充笔记。

## 文件

- [中文翻译](translation.zh.md)
- [英文原文](original.en.md)
- [元信息](meta.json)
- [阅读笔记](notes.md)

## 来源

- 原文链接：https://buttondown.com/hillelwayne/archive/illegal-vs-unwanted-states/
- 作者：Hillel Wayne
- 发布日期：2026-04-28
- 记录日期：2026-04-30

## 摘要

文章区分了两类系统状态：

- **非法状态**：系统绝不应该进入的状态，对应被违反的不变式。
- **不想要的状态**：系统可以短暂进入，但不应该长期停留的状态。

核心观点是：很多工程师想通过类型或约束彻底排除的状态，其实应该被系统表示出来，因为现实世界、业务流程或用户意图可能会把系统推入这些状态。正确做法通常不是让它们不可表示，而是检测、提示并确保最终退出。
