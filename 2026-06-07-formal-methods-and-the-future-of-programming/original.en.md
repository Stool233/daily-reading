# Formal methods and the future of programming

> Source: https://blog.janestreet.com/formal-methods-at-jane-street-index/  
> Author: Yaron Minsky  
> Published: 2026-06-07

This file records source metadata and a detailed non-verbatim source map. The full article remains at the source link.

## Article Structure

- Jane Street had long been skeptical that full formal methods were worth the cost for most of its software, while still valuing type systems as a lightweight formal method.
- The article uses seL4 as an example of a successful but very expensive verification effort: 25 person-years to verify 8,700 lines of C, with roughly 23 proof lines per code line and about half a person-day per verified line.
- Agentic coding changes the cost-benefit analysis: models lower the practical cost of using proof tools, and model-generated code makes verification more important.
- Formal methods can reduce the human review burden and provide strong feedback signals to agents, both during use and during training.
- Tests, property-based tests, and fuzzing remain valuable, but they do not provide the same universal guarantees that type systems and proof techniques can offer.
- Jane Street believes it has two advantages: deep control over the language it uses and a programming culture unusually receptive to advanced type-system and language ideas.
- The company wants to build on external formal-methods ecosystems such as Lean, Dafny, Rocq, Agda, and Iris, while also exploring techniques that require co-designing the language and proof methods.
- The post closes with a hiring invitation for formal-methods work in London and New York.

## Detailed Source Map

### Opening Position

The article starts with a reversal. For many years, Yaron Minsky told people that Jane Street was not interested in formal methods as an organizational priority. He now says that is no longer true.

The change is not framed as a simple admission that the old position was wrong. Jane Street has always valued tools that improve software reliability, and type systems are treated as a practical, lightweight form of formal reasoning. Since the company has benefited greatly from advanced type systems, one might expect it to have embraced heavier formal methods earlier.

The historical objection was cost. Outside special cases such as hardware synthesis, full formal verification seemed too expensive relative to the value it would provide for most production software. The seL4 microkernel is presented as both an impressive achievement and a warning about effort: the proof work took many person-years and required far more proof text than implementation code.

That tradeoff can make sense for a security-critical microkernel, where the specification is relatively crisp and the stakes justify the investment. Jane Street's view had been that the same tradeoff did not work for most of its software, including critical internal systems.

### Why Agentic Coding Changes the Calculation

The article's main claim is that agentic coding changes both sides of the cost-benefit equation.

On the cost side, AI agents make formal methods easier to use. The point is not that agents can automatically solve arbitrarily hard proofs. Humans still need to guide the proof strategy, understand why a system should be correct, and decide what should be specified. But models can help with the detailed mechanics of writing proofs and interacting with proof systems, which broadens the population of programmers who can use these tools productively.

On the benefit side, generated code increases the importance of verification. Models are increasingly good at producing useful code, but that code is not automatically code a team should ship. It can be overcomplicated, contain subtle bugs and edge cases, and miss invariants that matter inside a particular codebase. Human reviewers therefore spend substantial time checking whether agent-produced code is acceptable. Formal methods could reduce that burden by giving reviewers stronger, more objective evidence.

Formal methods also matter because agents improve when they receive feedback. This applies both to reinforcement-learning settings and to day-to-day coding workflows. A failed proof obligation or violated specification gives an agent a precise signal that is often stronger than a natural-language review comment.

### Tests Are Useful But Not Sufficient

Minsky does not dismiss testing. The article explicitly values tests, property-based testing, fuzzing, and the testing infrastructure Jane Street has built.

The limitation is state-space coverage. Tests can sample behaviors, but they generally cannot cover every possible state a program might enter. Type systems demonstrate why universal guarantees matter. If a type system can rule out a class of data races, then the programmer gets a broad guarantee rather than a set of examples that happened to pass.

The same idea applies to security and correctness properties. If a type-level design makes cross-site scripting impossible in a given surface, that is qualitatively different from testing many input cases and hoping no exploit path remains.

The article treats advanced type systems as a proof of concept for agent-era formal methods. Jane Street has seen how valuable types are when agents write code: they narrow the search space, expose mistakes early, and produce machine-checkable feedback. This makes the company interested in stronger proof techniques that could provide even more leverage.

The post acknowledges escape hatches such as `Obj.magic`, which can bypass type constraints. But those exceptions can be tracked, restricted, and justified. Formal methods can also help document why a carefully chosen escape hatch is safe.

### Why Jane Street Thinks It Can Do This Internally

The article then asks why Jane Street is a good place to pursue this work, given that many startups and research groups are exploring agents and formal methods.

The first answer is language control. Jane Street has deep influence over the language environment it uses, especially through OxCaml. That makes it possible to modify the language to become a better host for proof-oriented techniques. Possible directions include modular specifications in the type system, constraints around ownership and mutability, and proof techniques integrated directly into the programming language.

The second answer is user culture. Minsky argues that many programming-language researchers find it easier to invent better language ideas than to persuade real users to adopt them. Jane Street's engineering culture is unusually receptive to new type-system features and language experiments. This creates an internal user base that can try near-term improvements while also supporting longer-term, more ambitious language-and-proof work.

This internal user base matters because formal-methods work needs feedback from serious production use. It allows Jane Street to test ideas in realistic software, learn from smaller improvements, and build toward more ambitious systems over time.

### Relationship To External Tools

The post does not propose ignoring the broader formal-methods community. It names several external ecosystems and tools as sources of inspiration, including Lean, Dafny, Rocq, Agda, and Iris.

Jane Street is interested in integrating OxCaml with existing tools where that is productive. At the same time, the article argues that some advantages may only appear when the programming language and the proof techniques are developed together. The strategic bet is therefore a mixture of integration with existing infrastructure and internal language/proof co-design.

### Closing

The article ends as a recruiting post. Jane Street is building a formal-methods team, with roles in London and New York, and frames the work as early-stage with a large amount still to build.

## Copyright Note

This archive intentionally does not reproduce the full copyrighted article. Use the source URL above for the complete text.
