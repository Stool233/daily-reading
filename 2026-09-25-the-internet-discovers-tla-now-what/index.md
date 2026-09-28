---
title: "The internet discovers TLA+. Now what?"
title_zh: "互联网发现了 TLA+，接下来呢？"
author: "Anna Mészáros, Szilvia Ujváry, Kseniia Strelbytska, Balázs Szilágyi, Ferenc Huszár"
source: "https://reasonable.io/blog/tla-tutorial/"
published: "2026-09-25"
recorded: "2026-09-26"
tags:
  - daily-reading
  - tla-plus
  - formal-methods
  - model-checking
  - liveness
  - refinement
  - verus
---

# The internet discovers TLA+. Now what? / 互联网发现了 TLA+，接下来呢？

本归档围绕状态模型、性质、证明与实现之间的关系组织阅读。中文导读包含简要提要与独立讲解，阅读笔记通过可运行实验讨论前提和结论。`translation.zh.md` 沿用归档文件名，内容是导读，不是逐段全文译文。

## 文件

- [中文导读](translation.zh.md)：概念、公式、状态图和实验结果。
- [阅读笔记与讨论](notes.md)：公平性、归纳不变量、精化与证明的可信边界。
- [原文导航](original.en.md)：原文、交互教程和补充资料。
- [可复现实验](examples/README.md)：自编 TLA+ 模型与七组检查配置。
- [Verus 延伸研究](verus-study.md)：同一语言中的规格、证明、Rust 实现，以及三份已验证程序。
- [限幅与规格语言设计](clamp-spec-design.md)：函数式定义如何对应谓词逻辑，以及与 TLA+ 的对照。
- [元信息](meta.json)。

## 来源

- 原文：[Reasonable 博客](https://reasonable.io/blog/tla-tutorial/)。
- 作者：Anna Mészáros、Szilvia Ujváry、Kseniia Strelbytska、Balázs Szilágyi、Ferenc Huszár。
- 发布日期：2026-09-25；阅读记录：2026-09-26。
- 随文教程：[TLA+ Playground](https://reasonable.io/figures/tla-playground)。

## 建议阅读顺序

先区分“满足某个安全条件”与“最终完成任务”，再比较相同模型在不同公平性条件下的结果。随后阅读归纳不变量的反例，理解可达状态检查与归纳步骤检查的不同。最后回到精化问题，检查一份证明究竟连接了哪些规格、假设和实际代码。

七组本地 TLC 实验均得到预期结果，其中三组有意触发反例。它们用于解释概念，不是对文章团队模型或 Verus 证明流水线的复现。

另对交互页公布的三节点选主模型进行了两组安全检查，复现了 38 个可达状态与重复投票的六步反例。检查配置与终止状态处理见[核对记录](examples/publisher-checks.json)。

2026-09-27 补充 Verus 研究：三个自编程序通过验证、编译和运行，五种故意引入的错误被拒绝。[说明与代码](examples/verus/README.md)

2026-09-28 补充限幅讨论：验证函数定义与谓词定义的等价性、存在唯一性、全称界限及另一种实现，并说明弱规格可能允许不符合完整需求的程序。[专题说明](clamp-spec-design.md)
