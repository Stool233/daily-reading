# Agent swarms and the new model economics

> Source: https://cursor.com/blog/agent-swarm-model-economics  
> Simplified Chinese edition: https://cursor.com/cn/blog/agent-swarm-model-economics  
> Author: Wilson Lin  
> Published: 2026-07-20  
> Note: This file is a non-verbatim source map. Read the linked article for the complete text, charts, and illustrations.

## Source map

### The experiment and the main claim

Cursor revisits a task that an earlier agent swarm handled poorly: implementing SQLite in Rust using only SQLite's 835-page documentation. The new and old swarms receive the same model configurations and time budgets, and progress is measured against a held-out SQL logic test suite.

The new harness performs better for every model mix. Cursor's working explanation is that swarm performance comes less from raw parallelism than from allocating context efficiently and engineering explicit coordination mechanisms.

### Trees, planners, and workers

Large goals naturally decompose into a tree. Planner agents, using the most capable models, retain the global view, make design decisions, split work, and delegate subtrees. Worker agents, usually using faster and cheaper models, concentrate their context on narrow leaf tasks.

This separation avoids forcing one long-running agent to remember both the whole plan and every implementation detail. The swarm topology is allowed to follow the shape of the task instead of being fixed in advance.

### A VCS designed for agent-scale concurrency

The earlier browser experiment peaked near 1,000 Git commits per hour; the newer system can peak near 1,000 commits per second. Cursor therefore built a VCS that is not only faster, but also acts as the control point where collisions become visible and coordination policies can run.

The article names five recurring failure modes and corresponding controls:

- Split-brain design: planners independently create incompatible versions of the same concept. Design decisions stay with planners, and delegated subtrees must not decide overlapping questions.
- Planner contention: planners repeatedly change the same areas according to incompatible views. Decisions move into shared design documents, with compile-checked references from dependent code and a reconciliation step for contradictory documents.
- Merge conflicts: workers are poor at absorbing another worker's context during a collision. A neutral third-party agent resolves conflicts for all sides.
- Megafiles: popular files grow without an owner and become conflict hotspots. Workers can flag them; new commits pause while an outside agent decomposes the file.
- Ossification: agents avoid core changes learned to be risky in human-owned repositories. The harness permits narrowly scoped intentional breakage, records the reason, and lets compiler failures propagate the design change to dependent work.

### Review lenses and environmental memory

Long-running swarms accumulate errors, so Cursor tests multiple review lenses: full worker transcript, worker output only, codebase only, different models, and different reviewer behaviors. No single lens is complete, but low-correlation reviewers can combine into a stronger quality filter.

The Field Guide is an agent-owned folder whose index is injected into each new agent. Agents curate surprising lessons under a line budget so later trajectories can be shorter. Cursor connects this to stigmergy: agents coordinate indirectly by changing an environment that subsequently changes other agents' behavior.

### SQLite evaluation

The swarm receives the SQLite manual but not SQLite source code, the SQLite binary, the test suite, or internet access. It is graded with `sqllogictest`, which contains millions of queries with known answers. Cursor says it also reviews each run manually for shortcuts and uneven test-targeted construction.

Four planner/worker configurations are compared: GPT-5.5 for both roles, Grok 4.5 for both roles, Opus 4.8 with Composer 2.5, and Fable 5 with Composer 2.5. By the four-hour cutoff, the new runs score between 73% and 85%, compared with 11% to 77% for the old runs; all new configurations later reach 100%.

### Coordination evidence

The old Grok 4.5 run produces 68,000 commits before two hours, about seventy times the new run's rate, but this activity coincides with more than 70,000 merge conflicts. The new run records fewer than 1,000 conflicts over four hours.

The hottest old-run file sees 7,771 conflicts and edits from 1,173 agents, while the most contested new-run file sees 47 conflicts. The old package structure grows to 54 Rust crates, including three SQL implementations; the new structure settles at nine.

The final code is also smaller. In the Fable mix, both harnesses eventually pass the full suite, but the old version uses 64,305 engine lines versus 9,908. In the Opus mix, the old harness uses 19,013 lines for a 97% score, while the new one uses 4,645 lines for 100%.

### Model economics

Quality is broadly similar across the displayed model mixes, while total cost ranges from $1,339 for the Opus 4.8 and Composer 2.5 hybrid to $10,565 for GPT-5.5 alone. Workers consume at least 69% of tokens in every run and more than 90% in most runs.

Frontier intelligence is concentrated in decomposition, architecture, and difficult trade-offs. Once ambiguity has been converted into explicit instructions, cheap workers can perform most execution. GPT-5.5 workers alone cost $9,373, while the whole Composer worker fleet under Opus planning costs $411.

Planner price per token is not enough to predict total cost. Fable uses fewer planning tokens than Opus, but its workers consume several times as many tokens, making the full run more expensive. Planning quality creates a downstream multiplier.

### Specifications as the unit of work

The article describes a progression from autocomplete operating on lines, to early models operating on blocks, to agents operating on files and features. With swarms, the proposed unit becomes the specification.

Cursor compares the swarm to a compiler that lowers intent through a task tree into executable work. Unlike a compiler, each lowering step is probabilistic. The harness mechanisms in the article attempt to reduce semantic drift, but the scarce input remains an accurate description of intent.

## Copyright note

This archive intentionally does not reproduce the full article. Use the source URLs above for the complete prose, figures, and footnotes.
