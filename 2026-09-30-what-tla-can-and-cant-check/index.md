---
title: "What TLA+ can and can't check"
title_zh: "TLA+ 能检查什么，不能检查什么"
author: "Hillel Wayne"
source: "https://buttondown.com/hillelwayne/archive/what-tla-can-and-cant-check/"
published: "2026-09-30"
recorded: "2026-10-03"
tags:
  - daily-reading
  - tla-plus
  - formal-methods
  - temporal-logic
  - model-checking
  - reachability
  - hyperproperties
---

# What TLA+ can and can't check / TLA+ 能检查什么，不能检查什么

本篇独立阅读，聚焦性质的表达方式与检查边界。先辨认公式在谈哪些执行，再区分语言、模型和检查工具各自承担的工作。

## 文件

- [中文导读](translation.zh.md)：原文简要提要、时序公式和可达性示意图。
- [阅读笔记与讨论](notes.md)：历史、时间、跨执行比较，以及对文中技术表述的核对。
- [原文导航](original.en.md)：文章与补充查阅的一手资料。
- [元信息](meta.json)：来源、日期和核对范围。

`translation.zh.md` 沿用归档文件名，内容为中文导读，并非全文翻译。概念示例和补充分析均单独标明。本次进行了文献与工具文档核对，没有运行模型检查实验。

## 来源

- 原文：[What TLA+ can and can't check](https://buttondown.com/hillelwayne/archive/what-tla-can-and-cant-check/)。
- 作者：Hillel Wayne。
- 刊物：Computer Things，托管于 Buttondown。
- 发布日期：2026-09-30；记录日期：2026-10-03。

## 阅读顺序

先阅读导读中的公式表与三状态示例，理解“可能发生”和“必然发生”的区别。再读笔记，检查增加历史、时钟或第二份系统以后，原来的需求究竟变成了什么性质。
