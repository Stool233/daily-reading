# The software industry: annealing, but wrong

> Source: https://apenwarr.ca/log/20260531  
> Author: apenwarr  
> Published: 2026-05-31  
> Archive mode: source map only. Full text is available at the source URL.

## Source Map

This file preserves the article's structure and argument in English paraphrase form. It does not reproduce the full original text.

### Opening Claim

The article begins with a familiar engineering policy: keep pull requests small, focused, testable, and easy for humans to review. The author agrees that this policy often improves quality, but points out a hidden cost: a large feature split into many small pull requests can multiply reviewer context switches and stretch the review process.

### Annealing As The Central Metaphor

The author compares software evolution to simulated annealing. At high energy, a system can make large jumps through a search space. As energy drops, the jumps become smaller, improving stability and coherence. For mature software, this maps well onto cautious incremental change: small steps preserve structure and reduce breakage.

### Where The Metaphor Fails

Annealing is less helpful when a system needs to change shape quickly. Modern AI-assisted coding makes it cheap to generate large, interconnected changes. That can be dangerous because the output may be less coherent and harder to review, but it also reopens the possibility of exploring major redesigns that would previously have been too expensive to attempt.

### Aperture Example

The author describes implementing dollar-based spend quotas for Aperture. The feature required several interdependent pieces: grant syntax, pricing approximation, and quota enforcement. Those parts influenced each other during development, so the real discovery process could not happen in a clean sequence of tiny isolated patches.

After the system worked, the author split the result into a few large reviewable pieces rather than many artificially tiny ones. The point is not that large patches are always good; it is that some features require a high-energy exploration phase before they can be made reviewable.

### Mature Product Contrast

The article contrasts Aperture, a newer product, with core Tailscale, a mature product with high reliability expectations. In a mature system, the cost of large disruptive moves is much higher. The author frames this as a matter of choosing the right tool for the moment rather than a personality preference for speed or caution.

### AI Changes The Economics

AI lowers the cost of producing big changes, but it does not automatically make them safe. A team can now fork and explore many directions, create broader test suites, or try major rewrites more cheaply than before. Most large changes will still be bad, but rejecting a large generated experiment can now have a lower creation cost than rejecting a much smaller human-written change did in the past.

### Review Becomes The Bottleneck

The author argues that teams need better ways to review, reject, and refine large AI-generated changes. That implies more investment in automation, specifications, UX testing, CI/CD, and especially AI-assisted review workflows. If writing code becomes cheap and reviewing code becomes scarce, the development process should put stronger demands on code authors before human review.

## Related Links From The Article

- Simulated annealing: https://en.wikipedia.org/wiki/Simulated_annealing
- Aperture: https://aperture.tailscale.com
- Related apenwarr post on review context switching: https://apenwarr.ca/log/20260316
- Related apenwarr post on corporate reorgs and simulated annealing: https://apenwarr.ca/log/20161102
- Related apenwarr post on systems design: https://apenwarr.ca/log/20230415
