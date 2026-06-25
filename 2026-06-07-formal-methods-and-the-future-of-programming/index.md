---
title: "Formal methods and the future of programming"
title_zh: "形式化方法与编程的未来"
author: "Yaron Minsky"
source: "https://blog.janestreet.com/formal-methods-at-jane-street-index/"
published: "2026-06-07"
recorded: "2026-06-25"
tags:
  - daily-reading
  - jane-street
  - formal-methods
  - agentic-coding
  - programming-languages
  - oxcaml
  - type-systems
  - software-verification
---

# Formal methods and the future of programming / 形式化方法与编程的未来

这是一篇每日阅读记录，已拆分为多个文件，便于分别阅读、修改和补充笔记。

## 文件

- [中文详细译述](translation.zh.md)
- [英文来源结构图](original.en.md)
- [元信息](meta.json)
- [阅读笔记](notes.md)

## 来源

- 原文链接：https://blog.janestreet.com/formal-methods-at-jane-street-index/
- 作者：Yaron Minsky
- 发布日期：2026-06-07
- 记录日期：2026-06-25

## 摘要

Yaron Minsky 解释了 Jane Street 为什么从长期不看好“重量级”形式化方法，转向认真投入相关团队建设。核心原因不是他们过去低估了正确性工具，而是 agentic coding 改变了形式化方法的成本收益曲线：模型能降低写证明和使用证明工具的门槛，而生成式编程又让代码验证瓶颈变得更突出。

文章把形式化方法定位为 agent 时代的两类基础设施：一是帮助人类更有效地审核和约束模型生成的代码，二是给 agent 提供更强、更可组合的反馈信号。Minsky 强调测试、property-based testing 和 fuzzing 仍然重要，但它们无法替代类型系统和证明技术带来的“全称保证”。

Jane Street 认为自己适合在这个方向上投入，因为他们既能深度控制 OxCaml 这类内部语言演进，又有一批愿意使用高级类型系统和语言特性的工程师。文章最后也明确表示，他们会吸收 Lean、Dafny、Rocq、Agda、Iris 等外部证明生态的成果，而不是闭门造车。
