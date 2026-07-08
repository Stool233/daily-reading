# 用于自我改进的 Harness 工程

> 原文：[Harness Engineering for Self-Improvement](https://lilianweng.github.io/posts/2026-07-04-harness/)
> 作者：Lilian Weng
> 发布日期：2026-07-04
> 说明：以下为覆盖全文结构的详细中文译述。为尊重原文版权，它不是逐字全文翻译；完整英文原文请阅读来源链接。

## 从递归自我改进到 harness

文章从 recursive self-improvement 讲起，但没有把自我改进限定为“模型直接改写自己的权重”。在现代 AI 系统里，能力提升还可能来自训练流水线、部署系统、工具接口、上下文管理、评估系统和运行时架构。也就是说，模型之外的那层系统同样可能成为自我改进的对象。

Lilian Weng 把这层系统称为 harness。Harness 是围绕基础模型的执行系统：它决定模型如何思考和规划，如何调用工具，如何观察外部世界，如何管理上下文，如何保存产物，如何应用权限和安全规则，以及如何评估结果。

这个定义让 harness 从“prompt 模板”上升为“运行系统”。它更像一个操作系统或 runtime：对模型暴露简单接口，同时把工具、状态、权限、文件、反馈和执行流程组织起来。

## 三个设计模式

第一类模式是工作流自动化。Agent 需要一个能持续推进任务的循环：计划、执行、观察或测试、改进，再继续执行。这个循环不只是让模型多想几步，而是让模型能通过工具反馈和环境反馈调整自己的行动。

第二类模式是把文件系统作为持久记忆。长任务会产生大量中间产物，例如实验日志、代码 diff、错误输出、论文笔记、运行轨迹和失败记录。如果这些东西都塞进上下文窗口，系统会迅速变得昂贵、混乱且难以恢复。文件系统的价值在于给产物一个稳定地址，让 agent 只在需要时读取相关部分。

第三类模式是子 agent 和后台任务。主 agent 可以并行探索多个假设，或者把一些相对独立的任务交给子 agent 执行。但这里的关键不是简单并发，而是让并发可见、可检查、可恢复。子任务结果应该落在文件、日志和状态记录里，而不是只存在于短暂的聊天上下文中。

文章用 coding agent 作为具体案例。成熟的 coding agent 通常会有一组稳定工具：查找文件、读取文件、编辑文件、运行 shell 命令、接入 git 或语言服务器、读取外部上下文、生成 artifact，甚至启动其他 agent。Harness 决定这些工具如何暴露、如何限制、如何总结结果，以及 agent 如何从错误中恢复。

## Harness 与核心智能

文章没有把 harness 神化为模型智能的替代品。它更像一种互相促进的关系：更好的 harness 能释放现有模型能力，而更强模型又能减少 harness 的脆弱手工规则，让系统保持简洁。

Weng 的近期开局判断是：实用的自我改进更可能先发生在 harness 层，而不是模型直接改写自身权重。Harness 工程会朝“元方法论”发展，也就是优化产生好答案的机制，而不是只优化某一次回答本身。

不过，随着模型能力提升，一些 harness 里的技巧可能会逐渐被模型内化。Prompt engineering 的变化就是一个软版本：很多人工 prompt 技巧不再像早期那样关键，但目标、约束、上下文和评估仍然需要被清楚表达。

## 优化对象如何上移

文章把 harness 优化的对象按层级排列：先是 instruction，再是结构化 context，然后是 workflow，再到 harness code，最后甚至是 optimizer code。这个顺序很有启发，因为它描述了 agent 系统从“写好提示词”走向“优化运行机制”的过程。

在 context engineering 这一层，文章讨论了 ACE、MCE 和 Meta-Harness。ACE 把上下文看成一个会演化的 playbook，由生成、反思和整理三个角色维护。它的重点是用结构化条目来更新经验，而不是反复重写一个越来越长的大 prompt。

MCE 进一步把“如何管理上下文”的机制和“上下文里具体写了什么”分开。外层优化 skill 或上下文管理程序，内层则根据这个程序优化具体任务上下文。Meta-Harness 则把优化对象推进到代码层：用 coding agent 提出新的 harness 候选，让候选 harness 带着自己的源码、得分、轨迹和状态更新参与评估。

这一组工作共同说明：context 不是临时拼出来的字符串，而是 agent 系统里需要生命周期、数据结构和优化机制的核心资源。

## Workflow 设计与自动研究

文章接着看 workflow 设计。AI Scientist 把研究过程拆成想法提出、实验、分析、写作和评审。ScientistOne 强调每个研究声明都要能追溯到证据。Autodata 使用 challenger、weak solver、strong solver 和 verifier 来生成合适难度的训练与评估数据。

ADAS 把 agent 设计本身建模为搜索问题。一个 meta-agent 从已有方案中获得灵感，提出新的 workflow，用代码实现，评估效果，并把成功方案放回 archive。AFlow 则把 workflow 表示成图，用树搜索来探索改进版本。

这部分的底层判断是：workflow 的设计空间太大，不可能长期只靠专家手写。只要 workflow 被表示为代码，agent 就能参与提出、修改、评估和保存新的 workflow。

## 自我改进的 harness

STOP 是早期“改进 improver”的例子。它关注的不是只把某个解答做得更好，而是把产生改进的机制本身做得更好。这个思路可以自然迁移到 harness：如果 harness 是驱动 agent 执行和改进的机制，那么 harness 本身也可以被优化。

Self-Harness 则更直接：它先从失败中挖掘弱点，再根据弱点提出有边界的 harness 修改，最后用 held-in 和 held-out 数据验证修改是否有效。通过这个循环，系统可以学习到针对不同基础模型弱点的 harness 指令或机制。

但文章也明确提醒风险。如果一个程序能修改支配自身执行的系统，抽象边界就会被打破。可编辑表面必须被仔细设计，权限控制、安全层和关键评估器应该位于自我改进循环之外。

## Evolutionary search 与开放式改进

进化搜索适合大、怪、不容易求梯度但容易评估的搜索空间。Prompt、workflow、harness 和程序都符合这个特征。文章因此把 Promptbreeder、GEPA、AlphaEvolve、ShinkaEvolve、ThetaEvolve、Darwin Godel Machine、Hyperagents 等工作放进同一条线索里看。

这些系统的共同点是：保留候选方案，生成变体，执行评估，筛选更好的方案，再继续迭代。对 harness 来说，这意味着优化对象不只是自然语言 prompt，而是包含代码、工具、记忆、权限、工作流和评估逻辑的一整套可执行系统。

这也是文章最有力量、也最危险的地方。一旦 harness 成为可搜索空间，强 coding agent 就可以利用人类工程师使用的同一套设计空间。但如果评估器或权限边界设计不当，它也会更快地优化错误目标。

## 未来挑战

文章最后列出了一组很现实的瓶颈。

首先是评估器弱且模糊。很多研究任务和真实世界任务没有快速、精确的 verifier。研究品味、问题 framing、实验设计、长期科学价值，都很难被单一指标衡量。

其次是上下文和记忆生命周期。Agent 越自主，记忆越会增长。Harness 必须管理哪些内容进入上下文，哪些内容保留在外部状态，什么时候压缩、丢弃或复用。

第三是负结果。学术论文和训练数据天然偏向成功案例，但自我改进系统必须学会保存失败、承认失败，并知道何时放弃假设。失败记录能帮助缩小搜索空间。

第四是多样性坍缩。进化和强化学习循环容易快速利用当前高分模式，最后产生许多相似方案。开放式研究尤其需要保护看起来暂时低分、但可能通向新方向的探索。

第五是 reward hacking。系统会优化它得到的信号。如果奖励来自单元测试，它可能过拟合测试；如果奖励来自 judge model，它可能学会利用 judge 的偏差；如果奖励来自 benchmark，它可能利用 benchmark artifact。

第六是长期成功。Coding agent 能完成当前任务，不等于它会保护一个大型代码库的长期健康。可维护性、所有权边界、迁移成本、向后兼容和未来调试负担，都很难被短期 sandbox 训练捕捉。

最后是人的角色。Weng 的主张不是把人移出循环，而是让人上移到更合适的抽象层：在正确时间、用正确证据、对正确决策点提供监督。

## 术语对照

- **Harness**：围绕模型的运行系统 / 执行支架
- **Recursive self-improvement (RSI)**：递归自我改进
- **Context engineering**：上下文工程
- **Workflow automation**：工作流自动化
- **Persistent memory**：持久记忆
- **Sub-agent**：子 agent
- **Meta-methodology**：元方法论
- **Evolutionary search**：进化搜索
- **Reward hacking**：奖励黑客 / 奖励投机
- **Held-in / held-out**：内部验证集 / 外部留出集

## 核心脉络

1. 自我改进不必只理解为模型改写权重，部署系统和 harness 也是可改进对象。
2. Harness 是模型与现实任务之间的运行层，负责 workflow、工具、记忆、权限、评估和产物管理。
3. Harness 优化会从 prompt 走向 context、workflow、harness code，甚至 optimizer code。
4. Context engineering、auto-research、self-harness 和 evolutionary search 可以放在同一条“优化运行机制”的线索下理解。
5. 真正困难的部分是评估、记忆生命周期、失败记录、多样性、权限边界、长期质量和人类监督。
