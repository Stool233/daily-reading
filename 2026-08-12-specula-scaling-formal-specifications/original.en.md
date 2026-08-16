# Specula: Scaling formal specifications for autonomous model checking of system code

> Source: https://muratbuffalo.blogspot.com/2026/08/specula-scaling-formal-specifications.html  
> Author: Murat Demirbas  
> Published: 2026-08-12  
> Reviewed paper: https://arxiv.org/abs/2607.25333  
> Project: https://github.com/specula-org/Specula  
> Note: This file is a non-verbatim source map. Read the linked post for the complete text and figures.

## Source map

### What Specula automates

Specula uses coding agents to derive TLA+ specifications and invariants from system code and its surrounding artifacts. It validates implementation traces against the model, model-checks the specification for illegal concurrent behaviors, and attempts to reproduce a discovered counterexample in the implementation with a timing-sensitive integration test.

Demirbas is impressed by the end-to-end automation but frames the post as an argument with the paper: first identify the practical achievement, then ask what kind of specification and assurance the system actually provides.

### Scale and reported results

Specula is evaluated on slices of 48 open-source distributed and concurrent systems, including MongoDB, SONiC, libgomp, Etcd, and RabbitMQ's `ra`, across seven implementation languages. It reports 249 bugs, 207 of them new. End-to-end runs take 1.4 to 9.8 hours, with a median token cost of $57 per system.

On a five-system comparison, raw Claude Code finds two bugs, Claude Code equipped with official TLA+ skills and MCP tools finds three, and Specula finds 62. Demirbas reads this gap as evidence that tool knowledge alone is insufficient; runtime feedback that repairs generated artifacts is the main contribution.

### Two opposing feedback forces

Trace validation pulls the specification toward observed code behavior. Model checking pushes against changes that introduce illegal states. Either signal can fail alone: optimizing only for trace replay invites agents to weaken guards, add wildcards, or hard-code updates, while an abstract model without code traces can drift away from the implementation.

Specula places counterexamples, trace gaps, and failed code-level reproductions into self-evolving loops. Each iteration supplies new evidence and asks the agent to revise its model, invariant, instrumentation, or bug interpretation.

### The intent and circularity problem

The system treats code, comments, commits, pull requests, issues, and documentation as evidence for intended behavior. The post reports that 87% of invariants can be traced to code or comments, 74% to issue trackers, and 20% to documentation; these categories can overlap.

Demirbas's objection is that implementation artifacts are also where bugs live. If model correctness is judged against code and code correctness is judged against the model, the process needs a separate reference for intent. It can expose contradictions among artifacts, but a consistently documented design error can be absorbed as intended behavior. An ambiguous comment can also cause a real invariant to be relaxed without a visible failure.

This differs from the traditional Lamport-style workflow, where an independently authored requirements specification helps create understanding before implementation. Specula runs the direction backward by reconstructing understanding from an existing codebase.

### Scenario models and soundness questions

Full reference models are too large for exhaustive model checking, so Specula projects them into scenario models. It bounds how often actions can execute, coarsens multi-step processes into atomic actions, and fixes an order between selected action pairs.

Human modelers also use these state-space reductions, but Demirbas argues that their property-preservation conditions are not made explicit. Coarsening is safe only for properties that do not depend on hidden intermediate states. Without such justification, scenario checking can look closer to intelligent fuzzing guided by inferred specifications than to comprehensive verification.

### Protocol-level and code-level invariants

The paper distinguishes invariants that should hold for every conforming implementation from invariants describing this particular codebase. The former can provide a signal more independent of the current implementation.

Only 21.1% of the generated invariants are protocol-level, while 78.9% are code-level. The agent decides the category, and the post sees no obvious structural distinction that makes the classification independently checkable. A misclassified implementation description can therefore become the very guard intended to prevent overfitting to implementation behavior.

### Convergence and ambiguous counterexamples

The paper's convergence argument assumes agents improve across iterations. Empirically, all recorded runs converge: instrumentation is repaired within three rounds, 91.3% of invariant and model errors are fixed in one iteration, and none require more than four.

The four-round case concerns SONiC's link manager. An invariant says two gateways should never both be on standby, but model checking repeatedly finds legal temporary and degraded states where they are. The loop eventually repairs the invariant, illustrating both the value of counterexample feedback and the difficulty of distinguishing a real bug from a transient state that merely looks wrong.

### Dependence on model capability

Opus 4.8 performs much of the semantic work. Replacing it with Sonnet 4.6 reduces the five-system result from 62 bugs to 10 at similar wall-clock time and 61% of the cost, producing a worse cost per bug. Haiku 4.5 finds none and often stops early. It still reaches high TLA+ syntax correctness, but performs poorly on invariants.

The post interprets this gap as evidence that syntax generation is not the bottleneck. Extracting intended invariants and revising them from counterexamples requires stronger semantic judgment.

### The unsolved composition problem

Specula focuses on monolithic cross-sections rather than compositional specifications. In a multi-service system such as SONiC, it builds models per module and mocks cross-service interactions inside scenarios. It does not use assume-guarantee reasoning to establish that module-level guarantees compose into a system-level guarantee.

Demirbas considers this especially important because many serious distributed-system failures emerge across service and recovery boundaries. The post closes by praising Specula's pragmatic bug-finding value and TLA+ contribution while asking for more precise names and claims around the assurance it provides.

## Copyright note

This archive intentionally does not reproduce the full article. Use the source URL above for the complete prose, figures, examples, and postscript links.
