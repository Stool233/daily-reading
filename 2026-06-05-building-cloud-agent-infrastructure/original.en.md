# Building cloud agent infrastructure: what's different, and what we learned

> Source: https://x.com/i/article/2062697992814313472
> Tweet: https://x.com/intuitiveml/status/2062699747224568212
> Author: Peter Pang
> Published: 2026-06-05
> Issue: https://github.com/Stool233/daily-reading/issues/6
> Note: This file records source metadata and a detailed non-verbatim source map. The full article remains at the source link.

## Article Structure

- The article contrasts desktop agent frameworks with cloud agent infrastructure.
- Desktop assumptions are simple: one user, one machine, one process, local files, environment variables, and human retry when something fails.
- Cloud agent systems lose those assumptions. Runs happen inside fresh sandboxes, on shared hardware, often triggered by schedulers, HTTP requests, or other agents while the user is absent.
- The first lesson is to separate slow-changing user-controlled environment state from fast-changing platform-controlled runner code.
- CREAO uses frozen sandbox snapshots to preserve the user's installed packages, files, downloaded data, and scripts.
- A deployment problem appears when the runner library is bundled into the same snapshot as the user's environment: the user wants stability, while the platform wants frequent runner updates.
- The eventual solution is to boot from the user's snapshot, hot-swap only the runner code, validate the replacement before use, avoid half-upgraded execution, and re-snapshot after successful runs when needed.
- The second lesson is to keep long-lived credentials outside the sandbox.
- Authenticated calls go through a host-side API bridge. The sandbox asks the bridge to perform a request, and the bridge attaches user credentials outside the sandbox boundary.
- The bridge uses layered checks: network-level allowlisting plus short-lived per-run JWTs scoped to a specific user, app, and session.
- The same bridge can also carry billing events, logs, and metrics, making it the only intentional crossing point between the sandbox and the platform.
- The final pattern is a single execution pipeline shared by UI clicks, scheduled jobs, API calls, and software-triggered runs.
- The article ends with a product-level framing: a cloud agent is a function with a natural language interface. The user's code and environment belong to the user, while trigger surfaces, runtime, and security boundaries belong to the platform.

## Detailed Source Map

### Desktop Assumptions Do Not Survive The Cloud

The article opens by describing the implicit world assumed by many agent frameworks. The agent runs on a laptop, shares the user's local environment, can use environment variables, writes to a local filesystem, and stops when the terminal or laptop stops. If a package is missing or a run fails, the user is present to fix or retry it.

Cloud infrastructure changes every one of those conditions. An agent run may start inside a new sandbox on shared hardware. The caller might be a scheduled job, a webhook, an API request, or another agent. The user may be asleep. Code inside the sandbox might be malicious or compromised. Persistence, identity, network trust, retries, and lifecycle management have to become explicit platform guarantees.

This is the article's main shift: cloud agent infrastructure is not simply a desktop agent moved to a server. It is a different trust and lifecycle model.

### Lesson 1: Separate Slow State From Fast Code

The first lesson concerns change cadence. On a desktop, the user's environment and the agent runtime are usually one thing. In the cloud, they have different owners and different update schedules.

The user's environment changes slowly and deliberately. An agent might install Python packages, download market data, write charting scripts, or accumulate other useful state. CREAO freezes that environment into a sandbox snapshot so future runs boot from the same bytes.

The platform runner changes quickly. It is the small harness library that coordinates the agent during a run, and the platform team may deploy it many times a day. If runner code and user state live in the same frozen image, deployments create a conflict: either keep old runner code or throw away the user's frozen environment.

The article describes an early blunt fix: discard the old snapshot when the runner version is stale. That worked for interactive use, but failed the contract expected by unattended runs. A scheduled run should not lose its environment just because the platform deployed moments earlier.

The eventual model borrows from operating-system boundaries. The user's environment is like a home directory; the runner is more like platform code that can be upgraded separately. Boot from the user's snapshot, stage a new runner, validate it, swap only the runner code, clear stale runtime cache, and kill the sandbox rather than continue if any step fails.

The general diagnostic question is: who controls the cadence of change for this artifact? If two owners with different cadences share one artifact, the system will eventually pay for that coupling.

### Lesson 2: Keep Credentials Outside The Execution Boundary

The second lesson is security. A desktop agent often acts as the user on the user's machine. A cloud agent is different: it runs on shared infrastructure, against the open internet, and executes code produced by an LLM from prompts that may be hostile.

The article's rule is that long-lived credentials should not enter the sandbox. The sandbox should not hold OAuth tokens, API keys, or other durable secrets in memory, files, or environment variables.

Instead, authenticated requests go through an API bridge outside the sandbox. The agent sends a local request to the bridge. The bridge verifies that the request is allowed, attaches the user's credential on the host side, forwards the request, and returns the response. The credential never crosses into sandbox memory.

The authorization model has two layers. The first is a network boundary: only sandbox hosts on an internal range can reach the bridge. The second is a short-lived JWT minted for each run, scoped to the user, app, and session, and expiring with the run window. If a sandbox is compromised, the attacker receives only a narrow, temporary capability, not a reusable credential.

The same bridge is also the path for billing deductions, logs, and metrics. This keeps the sandbox boundary simple: everything inside is treated as potentially compromised, and one controlled interface crosses the boundary.

### The Pattern Underneath

The article reduces the implementation to a small set of properties:

- User state lives in a frozen sandbox snapshot until the user changes it.
- Platform runner code can be hot-swapped independently of that state.
- Credentials live outside the sandbox.
- UI runs, scheduled runs, API-triggered runs, and software-triggered runs share one execution pipeline.

The last property matters for product velocity. If every trigger goes through the same execution path, billing, logs, metrics, retries, and security checks remain consistent. Adding a new trigger becomes a routing problem rather than a new architecture.

The article's final abstraction is that an agent in the cloud is a callable function with a natural language interface. The user owns the implementation and environment; the platform owns triggers, runtime, isolation, credentials, and safety boundaries.

## Copyright Note

This archive intentionally does not reproduce the full copyrighted article. Use the source URL above for the complete text.
