# 阅读笔记

## 一句话总结

很多看似应该被禁止的“非法状态”，其实只是“不想要的状态”：系统应该能够表示它们、检测它们，并引导它们最终被解决。

## 关键概念

- **Illegal state / 非法状态**：系统任何时候都不应进入。
- **Unwanted state / 不想要的状态**：系统可以短暂进入，但不应长期停留。
- **Invariant / 不变式**：非法状态通常对应不变式被破坏。
- **Liveness / 活性**：不想要的状态常常要求“最终会离开”。

## 可延伸思考

- 在业务系统里，哪些约束应该做成“无法表示”？
- 哪些状态虽然危险，但应该允许临时存在？
- 对用户而言，“明确告知正在进入不想要状态”是否比直接禁止更好？

## 我的摘录

> An illegal state is a state we never want our system to be in. An unwanted state is a state we don't want to stay in.

## 我的想法

- 待补充。
