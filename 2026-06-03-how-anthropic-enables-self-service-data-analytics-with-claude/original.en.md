# How Anthropic enables self-service data analytics with Claude

> Source: https://claude.com/blog/how-anthropic-enables-self-service-data-analytics-with-claude  
> Author: Chen Chang, Clement Peng, Justin Leder, Johanne Jiao, Josh Cherry  
> Published: 2026-06-03

This file records source metadata and a detailed non-verbatim source map. The full article remains at the source link.

## Article Structure

- Self-service analytics has historically created a tradeoff between wide, denormalized tables that become inconsistent and isolated user workspaces that create metric and dashboard sprawl.
- LLMs create a new path, but connecting an agent directly to a warehouse can make answers look more precise than they really are.
- Anthropic reports that Claude automates most internal business analytics queries with high aggregate accuracy, freeing the data team for higher-leverage work.
- The article argues that accuracy is mostly a context and verification problem, not a SQL-generation problem.
- It identifies three main error patterns: ambiguous mapping from business language to data entities, stale schemas or definitions, and failure to retrieve the right already-existing context.
- Anthropic's stack has four major layers: data foundations, sources of truth, Skills, and validation.
- The appendix gives a warehouse-skill template showing how procedural guidance can force semantic-layer usage, clarify scope, define data integrity rules, and route the agent to curated references.

## Detailed Source Map

### Opening Problem

The article starts from a familiar pain point in data organizations. Business stakeholders want answers without waiting for a data scientist or data engineer, but traditional self-service approaches tend to break down as the company grows.

One option is to expose very wide tables and denormalized views. That helps non-experts get started, but it often creates overlapping tables, inconsistent definitions, and multiple plausible ways to compute the same metric. Another option is to give teams isolated analytic environments. That can reduce central bottlenecks, but it misses many one-off business questions and encourages duplicated dashboards and metrics.

LLM agents seem to offer a third path: let users ask questions in natural language and let the model write and run the analysis. The article warns that this can produce a dangerous illusion. The answer may look crisp, while the user is now further away from the documentation, data expertise, and infrastructure constraints that previously kept analyses grounded.

Anthropic's framing is that the model's ability to generate SQL is not the bottleneck. The hard part is resolving the user's informal question into the correct, current, governed data entities and then validating that path.

### Why Analytics Differs From Software

The article contrasts coding agents with analytics agents.

In software engineering, there are often many valid implementations, and tests or type checks can provide partial guardrails. The model's creativity is useful because the solution space is broad.

Analytics is different. A business question often has one correct answer, tied to one correct source, one correct grain, one correct exclusion rule, and one correct time convention. There may be no deterministic test that proves the answer is right. A plausible answer can still be subtly wrong.

The main source of difficulty is ambiguity in the data model. The agent needs to map a stakeholder phrase to a specific business entity, metric, table, column, filter, and time window. If that mapping succeeds, SQL execution becomes the easier part.

The article groups inaccurate responses into three dominant failure modes:

- **Business-concept ambiguity**: the agent sees multiple plausible tables, fields, or definitions and cannot reliably choose the governed one.
- **Staleness**: schemas, sources, documentation, and business definitions change faster than static prompts or docs can keep up.
- **Retrieval failure**: the correct answer exists somewhere, but the search space is so large that the agent does not find the right reference.

### Agentic Analytics Stack

Anthropic's stack is designed to attack those three failure modes layer by layer.

Data foundations reduce ambiguity by creating canonical datasets and governed definitions. The article emphasizes that standard data-engineering practices still matter: dimensional modeling, shift-left tests, freshness checks, completeness checks, lineage, and metadata quality remain necessary.

The key difference is the end user. The data model is no longer consumed only by data experts. Agents acting for less technical users now need the warehouse to be legible. This changes the bar for metadata, ownership, canonicality, and enforcement.

The recommended practices are:

- Create fewer, better-governed canonical datasets instead of many near-duplicates.
- Enforce standards through tooling, CI, and organizational mandate.
- Keep modeling code, semantic definitions, reference docs, dashboard definitions, and skill files close enough that changes can be validated together.
- Treat metadata as a product, including grain, ownership, lineage, valid values, metric definitions, and tiering.

### Sources of Truth

The sources-of-truth layer gives the agent trusted surfaces to consult.

The semantic layer is the highest-trust path. If a user question maps to a defined metric, the agent should call the semantic layer and get the same number as the rest of the company. Anthropic recommends using Claude to draft documentation, but keeping human ownership over metric definitions.

Lineage and transformation graphs come next. When the semantic layer does not cover the question, lineage helps the agent understand which upstream models feed a concept, which models are deprecated, and which models share the needed grain.

The historical query corpus sounds attractive, but Anthropic found that raw retrieval over thousands of prior SQL files barely improved accuracy. Their interpretation is important: having access to the information is not enough. The agent needs structure that maps a new question to the right entity and method. Prior SQL should become curated domain docs and reusable patterns, not a raw source the agent searches directly.

Business context is the layer many teams skip. The agent needs to understand internal project names, product launches, team-specific meanings, decision logs, roadmaps, and organizational context so it can resolve ambiguous references and ask better clarifying questions.

### Skills

In this article, Skills provide procedural knowledge: which sources to consult, in what order, how to handle ambiguity, and what a complete analysis should include.

The article reports a large accuracy difference between using only the underlying environment and adding well-maintained Skills. The important lesson is not just that instructions help. It is that procedural routing and domain-specific references shrink the search space before the agent writes a query.

Anthropic describes a pairwise pattern:

- A knowledge skill acts as a top-level router into curated domain references.
- An analysis or execution skill encodes the senior-analyst workflow: clarify the request, choose sources, query, review, and present the result with limitations.

The reference docs are written for LLM retrieval. They emphasize grain, scope, exclusions, canonical tables, join keys, hygiene filters, gotchas, routing triggers, and neighboring domain docs. They avoid brittle recipes that will go stale as the data model changes.

Skill maintenance is treated as production engineering. When a reporting model changes, a review hook can require the corresponding skill or reference doc to change. The article says this reduced the decay of offline accuracy and made skill updates part of normal data-model development.

The same canonical skill content is also synced across surfaces, so answers remain consistent whether the user asks through an IDE, Slack, a dashboard tool, or another hosted agent surface.

### Validation

Validation is the mechanism that reveals which failure mode is still leaking through.

Offline evaluations are question-answer pairs. Anthropic uses dashboard-derived evals for common stakeholder questions and long-tail evals generated from business context and table docs, then human-validates them. Stakeholder corrections can also become candidate evals.

The article recommends anchoring ground truth so it does not drift: use snapshot dates, stable fact tables, or grade the query logic instead of a moving number. Evals should run in CI when a dependent model or skill changes.

Eval results should be stored like telemetry. Each run should preserve skill version, git SHA, model ID, assertion results, token counts, and latency, so the team can query whether a change actually improved the system.

Launches should be gated by domain. A domain owner should not roll out an analytics agent for their area until that area clears the expected eval threshold.

### Ablation

The article's ablation section is especially practical.

Anthropic holds a fixed eval set and changes one structural component at a time: which sources the agent can access, whether a reviewer sub-agent is worth the latency, whether docs should be split or merged, and similar decisions.

One negative result shaped the roadmap. Giving the agent broad direct access to thousands of dashboard, transformation, and notebook SQL files did not meaningfully improve accuracy. In many wrong cases, the answer existed in the corpus and the agent had read related material, but it still failed to use the information correctly. The bottleneck was structure, not raw access.

The article recommends running before-and-after evals at PR granularity and recording negative results so future contributors do not repeat failed experiments.

### Online Validation

Online validation catches production problems that offline evals miss.

Anthropic uses adversarial review to challenge assumptions before final answers, accepting higher token and latency costs when accuracy matters. It also attaches provenance to responses: source tier, freshness, owner, and review information. This does not guarantee correctness, but it helps consumers understand how much to trust an answer.

Data quality checks ensure that the referenced field is current, complete, and not anomalous. Passive monitoring tracks signals such as how often the semantic layer is used and how often users correct the agent. Active correction harvesting turns stakeholder corrections into doc fixes and new evals.

The article is candid about the remaining hard case: silent wrong answers. If a plausible wrong answer is accepted without objection, the system may not notice. Mitigations include provenance, human sign-off for leadership-facing work, and daily checks of top KPIs against blessed dashboards.

### Getting Started

The article's pragmatic starting point is modest: build a few canonical datasets, a few dozen evals, and a thin knowledge skill. The rest of the stack can grow as the system proves useful and the risk profile demands it.

Teams should decide how much infrastructure they need by considering risk tolerance, data-model complexity, audience expertise, cost and latency budgets, and access-control constraints.

The closing lesson is that the biggest gains come from addressing the three recurring failure modes: collapse ambiguity into governed answers, make those answers discoverable, and detect when they become stale.

## Copyright Note

This archive intentionally does not reproduce the full copyrighted article. Use the source URL above for the complete text.
