# The internet discovers TLA+. Now what? — source guide

- Article: [Reasonable](https://reasonable.io/blog/tla-tutorial/).
- Authors: Anna Mészáros, Szilvia Ujváry, Kseniia Strelbytska, Balázs Szilágyi, Ferenc Huszár.
- Published: 2026-09-25. Recorded: 2026-09-26.
- Interactive companion: [TLA+ Playground](https://reasonable.io/figures/tla-playground).

This file preserves source navigation rather than reproducing the article. The local WorkerProgress exercise is independently written and is not the playground's election model.

## Primary references consulted

- Leslie Lamport, [Specifying Systems](https://lamport.azurewebsites.net/tla/book-21-07-04.pdf), especially the discussion of stuttering and fairness in Chapters 2 and 8.
- [Verus repository](https://github.com/verus-lang/verus).
- Verus guide: [spec, proof, and exec modes](https://verus-lang.github.io/verus/guide/modes.html).
- Verus guide: [assert and assume](https://verus-lang.github.io/verus/guide/requires_ensures.html).
- Verus guide: [using LLMs to develop proofs](https://verus-lang.github.io/verus/guide/llmforverusproof.html).
- [Anvil repository](https://github.com/anvil-verifier/anvil).
- Alur, Henzinger, and Kupferman, [Alternating-Time Temporal Logic](https://www.cis.upenn.edu/~alur/Jacm02.pdf), JACM 2002; abstract consulted for the distinction between path and strategy quantification.

## Retrieval and verification

The article was retrieved directly over HTTPS after the web reader initially failed; a web-search result also exposed the publisher's article through its short link. The playground's public source was inspected, and its N=3 safety configurations were independently checked from temporary files. See [publisher-checks.json](examples/publisher-checks.json) for the exact scope and deadlock-check setting. Publisher liveness, scaling, and Verus-pipeline results were not independently reproduced.

See the [Chinese guide](translation.zh.md), [discussion](notes.md), and [local TLC results](examples/results.json) for the separate reading exercise.

## Verus follow-up, 2026-09-27

The [Chinese study](verus-study.md) adds three independently authored, verified programs and five intentional rejection experiments. See the [examples](examples/verus/README.md) and [recorded results](examples/verus/results.json).

Primary sources for this follow-up include the official guide pages on [embedding Verus in Rust](https://verus-lang.github.io/verus/guide/verus_macro_intro.html), [proof functions](https://verus-lang.github.io/verus/guide/proof_functions.html), [loops and invariants](https://verus-lang.github.io/verus/guide/while.html), [mutable references](https://verus-lang.github.io/verus/guide/mutable-references.html), and [trusted assumptions](https://verus-lang.github.io/verus/guide/tcb.html). Additional sources are linked at their relevant claims in the study.
