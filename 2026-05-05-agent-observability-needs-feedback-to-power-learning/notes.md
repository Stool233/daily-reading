# 阅读笔记

## 一句话总结

Agent observability 的价值不只是看见 agent 做了什么，而是把 trace 与 feedback 连接起来，形成持续改进 agent 行为的学习闭环。

## 关键概念

- **Trace as context**：trace 保存一次 agent 运行的上下文，包括输入、模型调用、工具调用、中间状态、输出和耗时。
- **Feedback as signal**：feedback 告诉系统这次行为是否满足目标，以及问题出现在哪个环节。
- **Observability to learning**：observability 从事后排查工具升级为改进 agent 的数据管道。
- **Harness**：模型外部的脚手架，包括 prompts、tool schemas、permission checks、control flow、memory update logic、routing、retries 和 guardrails。
- **Context learning**：改进 agent 能看到、存储、压缩或丢弃的信息，例如检索文档、记忆、用户偏好、工具结果、历史对话和环境状态。
- **Human correction**：人工修正不只是一次性补救，也可以沉淀为评估样本或示例。
- **Evaluation loop**：把线上反馈转为 eval dataset，用于检测新 prompt、模型、工具和 workflow 是否真的改进。

## 文章主张

1. 传统 observability 主要用于定位系统故障；agent observability 还必须支持行为学习。
2. Agent 的学习可以发生在模型层、harness 层和上下文层，不能只理解为训练模型权重。
3. 学习可以是人工驱动，也可以是系统自动采样、评分、路由和整理 trace。
4. Agent 的失败往往不是单一 error，而是目标理解、上下文检索、工具选择、计划执行或输出判断中的某个环节出了问题。
5. Trace 提供“发生了什么”的上下文，feedback 提供“好不好”的质量信号。
6. 只有把 feedback 绑定到 trace，团队才能把线上经验转化为可重复的评估和改进动作。
7. 未来的 agent observability 平台会越来越像 feedback、dataset、eval 和 deployment iteration 的中枢。

## 反馈来源

- **直接用户反馈**：点赞、点踩、星级评分、文字修正。优点是含义清楚，缺点是通常很稀疏。
- **间接用户反馈**：代码是否被接受、diff 是否被回滚、测试是否通过、工单是否重开、答案是否被复制、用户是否重复提问。优点是量大，缺点是噪声更高。
- **LLM-as-judge**：用模型评估回答是否有帮助、是否遵循策略、轨迹是否可疑。适合规模化线上评估，但需要校准。
- **确定性规则**：用规则或正则表达式捕捉已知失败模式。便宜、稳定、可解释，适合不需要模型判断的信号。

## 平台能力

- **Store traces**：记录 agent 的完整执行轨迹，包括模型调用、工具调用、输入、输出、metadata、timing、errors 和 intermediate state。
- **Store feedback**：把反馈直接挂到 run、trace 或 thread 上，而不是放在独立表格或脱节的 analytics 系统里。
- **Generate feedback**：通过规则、evaluators、sampling、annotation queues、alerts 和 historical backfills 生成结构化反馈。

## 我的理解

这篇文章实际上是在重新定义 agent 平台的控制面。

如果把 agent 看成传统后端服务，observability 的目标是 debug：看日志、看 trace、看报错。但 agent 的核心问题不是“服务有没有响应”，而是“它是否以可接受的方式完成了任务”。这个判断通常无法只靠系统指标完成，需要用户反馈、人工审核和任务结果共同决定。

所以 trace 和 feedback 必须绑定。单独的 trace 只能告诉我们 agent 查了什么、调用了什么工具、输出了什么；单独的 feedback 只能告诉我们用户喜欢或不喜欢。把两者放在一起，才知道用户不满意到底是因为检索错了、工具错了、推理错了、还是 final answer 表达错了。

这也是 LangSmith 这类产品的战略位置：它不只是 observability dashboard，而是 agent 改进流水线。生产中的每一次交互都可能成为未来 eval 的样本；每一次人工修正都可能成为 prompt 或 policy 的训练信号。

## 对产品和工程的启发

- Agent 产品需要在设计初期就规划 feedback schema，而不是上线后只加一个 thumbs up/down。
- Trace 粒度要足够细，能把反馈定位到具体步骤，而不是只挂在最终输出上。
- 用户反馈、人工审核、自动 eval 应该进入同一个数据模型，否则很难形成长期学习资产。
- 线上反馈不能直接等同于训练数据，需要清洗、去重、归因和版本管理。
- Prompt、tool、workflow 的每次变更都应该能用同一批 eval 回归验证。

## 可延伸思考

- 什么样的 feedback 最适合 agent 产品：显式评分、用户改写、人工审核，还是任务成功率？
- 如何区分“用户不喜欢结果”和“agent 实际失败”？
- Feedback 应该绑定到整条 trace，还是绑定到 trace 中的具体 step？
- Agent observability 平台是否会成为新的 MLOps / DevOps 交叉层？
- 对个人或小团队来说，最小可行的 feedback-to-eval loop 应该长什么样？

## 我的摘录

> A trace tells you what happened.

> Store feedback with your traces.

## 待补充问题

- LangSmith 当前支持哪些 feedback 类型和 dataset/eval 工作流？
- Feedback 如何在多 agent、多工具、多步骤任务里做 attribution？
- 对长期运行的 agent，反馈是否应该影响 memory，还是只影响离线评估与发布流程？
