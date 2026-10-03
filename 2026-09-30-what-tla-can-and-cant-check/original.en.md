# What TLA+ can and can't check — source guide

- Article: [What TLA+ can and can't check](https://buttondown.com/hillelwayne/archive/what-tla-can-and-cant-check/).
- Author: Hillel Wayne.
- Publication: Computer Things, hosted on Buttondown.
- Published: 2026-09-30. Recorded: 2026-10-03.

This file preserves source navigation rather than reproducing the article. The [Chinese guide](translation.zh.md) contains a short synopsis and separately attributed explanations. The [reading notes](notes.md) distinguish the author's claims from additional analysis and documentation checks.

## Primary references consulted

- Hillel Wayne, Learn TLA+: [Temporal Properties](https://learntla.com/core/temporal-logic.html) and [Action Properties](https://learntla.com/core/action-properties.html).
- Hillel Wayne, Learn TLA+: [Auxiliary Variables](https://learntla.com/topics/aux-vars.html).
- Leslie Lamport and Stephan Merz: [Auxiliary Variables in TLA+](https://lamport.azurewebsites.net/tla/auxiliary/auxiliary.html), introductory project page.
- Leslie Lamport: [Specifying Systems](https://lamport.azurewebsites.net/tla/book-21-07-04.pdf), Chapter 9, especially sections 9.1–9.2 on real-time specifications.
- TLA+ project: [reachability feature proposal, issue #860](https://github.com/tlaplus/tlaplus/issues/860), [documentation PR #1400](https://github.com/tlaplus/tlaplus/pull/1400), and [the merged `_POSSIBLE` documentation](https://github.com/tlaplus/tlaplus/blob/0894c3407f4717fec7cc18bde3bf3c857fa47333/docs/possible-conditions.md).
- Hillel Wayne: [Hypermodeling Hyperproperties](https://www.hillelwayne.com/post/hyperproperties/).
- PRISM manual: [The P Operator](https://www.prismmodelchecker.org/manual/PropertySpecification/ThePOperator).

## Retrieval and verification

The article was read through the web reader and retrieved directly over HTTPS. Its canonical URL and visible publication date were inspected. The original HTML is not included in this archive; its retrieval checksum is recorded in [meta.json](meta.json).

The `_POSSIBLE` documentation link is pinned to merge commit `0894c3407f4717fec7cc18bde3bf3c857fa47333`, merged on 2026-08-11. A local TLC source checkout also contains the `_POSSIBLE` configuration token. These checks establish the documented spelling, not compatibility with every released TLC version. No TLC or PRISM model was executed for this reading.
