# Agent 可观测性需要反馈来驱动学习

> 原文：[Agent Observability Needs Feedback to Power Learning](https://www.langchain.com/blog/agent-observability-needs-feedback-to-power-learning)  
> 作者：Harrison Chase  
> 发布日期：2026-05-05  
> 说明：以下为覆盖全文结构的详细中文译述。为尊重原文版权，它不是逐字全文翻译；完整英文原文请阅读来源链接。

## 开篇：可观测性不只是调试

很多团队一开始会把 agent 可观测性理解成调试工具：某次运行出错了，于是打开 trace，逐步检查 agent 做了什么，再找出它在哪一步做了错误决策。

这种用法当然有价值，但作者认为它太窄了。Agent 可观测性的更深层作用，是支撑系统学习。单靠 traces 不能自动形成学习闭环，还需要 feedback，也就是能说明 agent 行为是否有用、是否被接受、是否被拒绝、是否低效、是否有风险、是否错误的信号。

这里说的学习，不只是模型训练意义上的学习。作者强调，agent 系统的学习发生在整个系统中：模型应该如何行动，harness 应该怎样引导模型，agent 需要什么上下文，哪些失败模式反复出现，哪些行为真的对用户有效。Trace 不是单纯的运行记录，feedback 也不是最后附上的一个评分。两者结合起来，才是改进 agent 系统的原材料。

## 学习发生在多个层次

作者首先说明，agentic system 可以通过多种方式随时间改进。学习并不只等于更新模型权重，它至少可以发生在模型层、harness 层和上下文层。

模型层的学习比较接近传统机器学习。如果团队在 traces 中发现模型持续误分类某类请求、经常选择错误工具，或者无法遵守某条策略，那么这些 trace 可以变成训练或强化学习材料，用于 SFT 或 RL，从而更新模型本身。

第二层是 harness。Harness 指模型外部的整个脚手架，包括 prompts、工具 schema、权限检查、控制流、记忆更新逻辑、路由、重试机制和 guardrails。Trace 可能显示：模型本身具备完成任务的能力，但外部脚手架没有给它正确约束或引导。比如工具描述可能有歧义，agent 可能需要“写入前必须读取”的约束，系统 prompt 可能在某个 tradeoff 上给了错误倾向。

第三层是上下文。Agent 对它接收到的信息非常敏感，这些信息包括检索到的文档、memory、用户偏好、工具结果、前几轮对话以及环境状态。Trace 有时会显示：模型在给定上下文下做出了合理选择，但上下文本身是错误的、不完整的或过时的。这时学习闭环要改进的不是模型，而是应该检索、保存、压缩或丢弃什么上下文。作者指出，这一类问题通常会被归入 memory。

这一节的关键点是：上述所有学习闭环都依赖 traces。团队必须知道 agent 看到了什么、做了什么、接下来发生了什么，才能可靠地判断应该改进模型、harness 还是上下文。

作者也因此把 agent observability 和 agent evaluation 连接起来。Trace 是 agent 行为变得可见的地方，也就是评估和改进开始的地方。

## 学习可以自动化，也可以由人驱动

接着，作者区分了手动驱动的学习和自动化学习。

有些学习是手动发生的。开发者查看 trace，发现 agent 调用了错误工具，于是修改 prompt 或 tool schema。产品经理回看一组失败对话，意识到产品需要新增一个 workflow。标注人员给 traces 打标签，帮助团队构建更好的评估数据集。这些活动都有人工参与，但它们仍然是学习。

另一类学习是自动化的。系统可以从生产 traces 中采样，运行线上评估，检测已知失败模式，把样本加入数据集，或者在某些异常看起来不对时触发审核队列。作者特别强调：学习闭环自动化，并不要求 agent 必须自动改进自己。自动化可以只是识别哪些 traces 值得关注，并把它们转化为结构化 feedback。

不管是人工驱动还是自动化驱动，整个过程都由 traces 支撑。如果只有一个低流量 agent，人工 review 可能已经足够。但当团队有很多 agents，或者面对高流量生产环境时，这就变成基础设施问题：平台需要捕获 traces、过滤 traces、给 traces 打分、把它们路由给合适的人或系统，并保存那些真正重要的样本。

## Traces 必要，但不充分

Trace 能告诉你发生了什么，但它本身不能告诉你这件事好不好。

这个区别很关键。一个 agent 可能花 40 步完成任务，但理想情况下也许 6 步就够了。它可能给出一个自信的最终答案，但用户实际上拒绝了这个答案。它可能没有抛出错误，却没有完成用户真正想要的目标。它也可能调用了正确工具，但传入了细微错误的参数。

所以，要从 traces 中学习，就必须把 feedback 挂到 traces 上。

Feedback 会把 observability 从被动记录变成训练信号、调试信号、产品信号或评估信号。没有 feedback，团队只是拥有大量运行轨迹；有了 feedback，团队才开始能提出有用问题：哪些 traces 代表成功？哪些 traces 代表失败？失败是由模型、harness 还是上下文导致的？哪些失败值得变成 evals？哪些行为正在随时间改善？

作者在这里给出的核心要求是：要把 feedback 和 agent observability 数据存放在一起。

## Feedback 可以来自很多地方

Feedback 不等于人工给每条 trace 打分。实际系统里的有效 feedback 有多种来源。

最直观的是直接用户反馈，比如点赞、点踩、星级评分或文字修正。这类信号容易理解，但通常很稀疏，因为多数用户不会主动留下明确反馈。

第二类是间接用户反馈。对于 coding agent 来说，这可能包括生成代码被接受的行数、diff 是否被回滚、编辑后测试是否通过、用户是否保留了生成改动。对于客服 agent 来说，这可能是用户是否重新打开工单。对于 research agent 来说，这可能是用户是否复制答案，或者是否又问了同一个问题。这类信号比显式评分更嘈杂，但数量通常多得多。

第三类是用 LLM-as-judge 生成反馈。Judge 模型可以评估回答是否有帮助，agent 是否遵守策略，或者某条 trajectory 是否可疑。它的价值在于可以规模化运行，尤其适合作为生产 traces 上的在线评估器。作者同时提醒，这种方式并不完美，需要校准，但它让团队可以在人工审核太慢的地方生成结构化 feedback。

第四类是确定性反馈，也就是规则和正则表达式。作者认为这类方法被低估了。如果团队已经知道某个失败模式，就应该把它编码下来。如果 agent 永远不应该在没有批准时调用破坏性命令，就检查这种情况。如果回答必须包含引用，就验证引用是否存在。如果 coding agent 显示出用户沮丧的迹象，也可以检测这种信号。

原文用 Claude Code 泄漏事件举例：一些报道提到 Claude Code 使用 `userPromptKeywords.ts` 中的正则表达式检测用户 prompt 里的沮丧词语。作者引用这些报道，是为了说明一个工程上的教训：不是每个 feedback signal 都需要一次模型调用。如果便宜的规则能捕捉有用信号，就使用便宜规则，同时要清楚记录这个信号如何被保存和使用。

## 可观测性平台需要什么

如果 observability 要支撑学习，那么平台至少需要三类能力。

第一，它需要存储 traces。这是基础层。平台要保存 agent 的完整执行轨迹，包括模型调用、工具调用、输入、输出、metadata、timing、errors 和 intermediate state。理想情况下，平台应该能从任意技术栈接入 traces，而不是只支持单一框架。作者提到 LangSmith 支持来自 30 多个框架的 tracing，也可以通过 OpenTelemetry 兼容应用接入 traces。

第二，它需要存储 feedback。Feedback 不应该放在一个与 trace 脱节的 spreadsheet 或 analytics system 里，而应该直接挂到它评价的 run、trace 或 thread 上。这样团队才能按 feedback 过滤数据，对比好轨迹和坏轨迹，从真实失败中构建数据集，并追踪某次变更是否改善了真正重要的行为。作者提到 LangSmith 支持捕获 feedback 并将其与 traces 关联。

第三，它需要生成 feedback。有些反馈来自用户，但大量有用反馈应该由系统自己产生。这包括规则、evaluators、sampling、annotation queues、alerts，以及对历史 traces 的 backfill。作者提到 LangSmith 支持 automation rules 和 online evaluations，包括运行在生产 traces 上的 LLM-as-judge evaluators。

这一节总结出的产品形态很明确：agent 团队需要的平台，不只是 trace viewer，而是能存储 traces、存储 feedback、生成 feedback 的系统。

## 学习闭环依赖 traces 与 feedback 的结合

文章最后回到主线：observability 的目的不只是查看 traces，而是从 traces 中学习。

Traces 告诉团队发生了什么，feedback 告诉团队这件事意味着什么。两者结合起来，团队才能改进模型、harness 和上下文；才能支持人工调试和自动化评估；才能把生产行为转化为 datasets、rules、alerts 和 regression tests。

没有 feedback 的 agent observability 是不完整的。团队虽然可以检查行为，却无法系统性地从行为中学习。要让 agent observability 发挥最大价值，就要把 feedback 和 traces 存放在一起。这样，agent traces 才不只是 logs，而会成为学习系统的一部分。

## 术语对照

- **Agent observability**：Agent 可观测性
- **Trace**：执行轨迹
- **Feedback**：反馈
- **Evaluation / eval**：评估
- **Harness**：模型外部脚手架 / 运行框架
- **Guardrails**：护栏 / 约束机制
- **Human-in-the-loop**：人在回路中 / 人工参与
- **Dataset curation**：数据集整理
- **Learning loop**：学习闭环
- **LLM-as-judge**：用大模型作为评估器
- **Regression tests**：回归测试

## 核心脉络

1. Agent 可观测性的深层价值不是调试，而是让系统持续学习。
2. 学习发生在模型、harness 和上下文三个层面。
3. 学习既可以由人驱动，也可以由系统自动筛选、评分、路由和整理 traces。
4. Trace 只说明发生了什么，feedback 才说明结果是否好、是否有用、是否值得改进。
5. Feedback 可以来自显式用户反馈、隐式用户行为、LLM-as-judge 和确定性规则。
6. 可观测性平台需要存储 traces、存储 feedback，并能生成 feedback。
7. Traces 与 feedback 结合后，生产行为才能变成 evals、datasets、alerts、rules 和 regression tests。
