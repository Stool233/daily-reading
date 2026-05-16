# Agent Observability Needs Feedback to Power Learning

> Source: https://www.langchain.com/blog/agent-observability-needs-feedback-to-power-learning  
> Author: Harrison Chase  
> Published: 2026-05-05

This file records source metadata, a detailed non-verbatim source map, and short excerpts only. The full article remains at the source link.

## Short Excerpts

> A trace tells you what happened.

> Store feedback with your traces.

## Article Structure

- Agent observability is becoming less about seeing what happened and more about improving what happens next.
- Learning can happen at the model level, the harness level, and the context level.
- Learning can be hand-driven through developer, PM, or annotator review, or automated through sampling, online evaluations, failure-pattern detection, dataset creation, and review queues.
- Feedback can come from direct user ratings or corrections, indirect user behavior, LLM-as-judge scoring, and deterministic rules.
- An observability platform for agents needs to store traces, store feedback, and generate feedback.
- Traces plus feedback can improve the model, harness, and context, and can turn production behavior into datasets, rules, alerts, and regression tests.

## Detailed Source Map

### Opening

The article starts from the common use case for agent observability: a run fails, so the team opens a trace, inspects the agent's steps, and locates the bad decision. The author says this is useful but incomplete. The deeper purpose of observability is to support learning across the whole agent system. Traces alone are not enough; teams also need feedback that indicates whether behavior was useful, accepted, rejected, inefficient, risky, or wrong.

The author frames traces and feedback as the raw material for improving an agent. A trace should not be treated as a passive log, and feedback should not be treated as a detached rating. Together, they help teams understand what the model should do, how the surrounding harness should guide it, what context the agent needs, what failures repeat, and what behaviors work for users.

### Learning at Multiple Levels

The article identifies three layers where agent systems can learn.

At the model layer, traces can reveal repeated model mistakes such as misclassifying requests, choosing the wrong tool, or failing to follow policy. Those traces may become examples for SFT or RL and can ultimately affect model weights.

At the harness layer, learning applies to everything around the model: prompts, tool schemas, permission checks, control flow, memory-update logic, routing, retries, and guardrails. A trace may show that the model had the right capability, but the scaffolding around it gave poor instructions or weak constraints.

At the context layer, learning focuses on the information given to the agent: retrieved documents, memory, user preferences, tool results, prior turns, and environment state. A trace may show that the model made a reasonable decision from bad or missing context, so the system should improve what it retrieves, stores, compresses, or discards.

The author uses this to connect observability with evaluation: traces are where agent behavior becomes visible, and visibility is the precondition for knowing what to improve.

### Human-Driven and Automated Learning

The article then explains that learning does not need to be fully automatic. A developer can inspect a trace and update a prompt or tool schema. A product manager can review failed conversations and decide that the product needs a new workflow. An annotator can label traces so the team can build a better evaluation dataset.

Automated learning can also happen without the agent rewriting itself. A system can sample production traces, run online evaluations, detect known failure patterns, add examples to datasets, or trigger review queues. In this framing, automation is often about identifying the traces that deserve attention and turning them into structured feedback.

For a low-volume agent, manual review may be enough. For many agents or high-volume traffic, the work becomes an infrastructure problem: capture traces, filter them, score them, route them, and preserve the important ones.

### Traces Are Necessary but Insufficient

The article emphasizes that a trace shows what happened, but not whether the behavior was good. An agent can complete a task in too many steps, produce a confident answer that the user rejects, avoid an explicit error while failing the user's intent, or call the correct tool with subtly wrong arguments.

To learn from traces, feedback must be attached to them. Feedback turns observability into a training, debugging, product, or evaluation signal. With feedback, teams can ask which traces represent success, which represent failure, whether failures come from the model, harness, or context, which failures should become evals, and which behaviors are improving.

### Sources of Feedback

The article lists several feedback sources.

Direct user feedback includes thumbs up, thumbs down, star ratings, and written corrections. This signal is easy to interpret, but sparse.

Indirect user feedback includes behavioral signals. For coding agents, this could include accepted lines of code, reverted diffs, passing tests, or whether the user kept the generated change. For support agents, it could include reopened tickets. For research agents, it could include whether the answer was copied or whether the user asked the same question again. These signals are noisier but more plentiful.

LLM-as-judge feedback can score usefulness, policy-following, or suspicious trajectories. It is useful at scale, especially as an online evaluator over production traces, but should be calibrated.

Deterministic feedback includes rules and regular expressions. If a team already knows a failure pattern, it can encode that pattern directly. The author uses reports about Claude Code's regex-based frustration detection as an example of a cheap rule capturing a useful signal without needing an LLM call.

### Platform Requirements

The article says that if observability is going to power learning, the platform needs three things.

First, it needs to store traces: model calls, tool calls, inputs, outputs, metadata, timing, errors, and intermediate state. Ideally, it should ingest traces from many frameworks and OpenTelemetry-compatible applications.

Second, it needs to store feedback. Feedback should be attached directly to the run, trace, or thread that it evaluates, rather than living in a disconnected spreadsheet or analytics system. This makes it possible to filter by feedback, compare good and bad trajectories, build datasets from real failures, and track behavior changes over time.

Third, it needs to generate feedback. Some feedback comes from users, but systems should also produce feedback through rules, evaluators, sampling, annotation queues, alerts, and backfills over historical traces. The article points to LangSmith automation rules and online evaluations as examples.

### Conclusion

The final argument is that the purpose of observability is not simply to inspect traces. The purpose is to learn from them. Traces explain what happened; feedback explains what it meant. Together, they help teams improve the model, harness, and context, support manual debugging and automated evaluation, and turn production behavior into datasets, rules, alerts, and regression tests.

## Copyright Note

This archive intentionally does not reproduce the full copyrighted article. Use the source URL above for the complete text.
