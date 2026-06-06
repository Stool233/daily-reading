# The 2026-07-28 MCP Specification Release Candidate

> Source: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
> Authors: David Soria Parra, Den Delimarsky
> Published: 2026-05-21

This file records source metadata, a detailed non-verbatim source map, and short excerpts only. The full article remains at the source link.

## Short Excerpts

> a stateless core

> Extensions Become First-Class

> Release Timeline and Validation

## Article Structure

- The release candidate for MCP `2026-07-28` introduces a stateless protocol core, a formal extensions framework, MCP Apps, the Tasks extension, authorization hardening, deprecations, JSON Schema upgrades, and governance changes.
- The main protocol shift removes the old initialize flow and protocol-level session ID. Request metadata moves into each request so any server instance can handle it.
- Server-to-client interaction is redesigned around active client requests and multi-round-trip results rather than an always-open session.
- HTTP traffic becomes easier to route, cache, and trace through required operation headers, cache metadata, and documented trace context propagation.
- Extensions become independently versioned, reverse-DNS identified, and managed through a formal SEP track. MCP Apps and Tasks are the two official extensions in this release.
- Authorization changes align MCP deployments more closely with OAuth 2.0 and OpenID Connect practices.
- Roots, Sampling, and Logging are deprecated under a new lifecycle policy, but they continue to work in this release.
- Tool schemas move to full JSON Schema 2020-12, and a resource error code changes to the JSON-RPC standard invalid-params code.
- The release candidate was locked on 2026-05-21; the final specification is planned for 2026-07-28.

## Detailed Source Map

### Opening

The article frames `2026-07-28` as the largest MCP specification revision since launch. Its practical theme is operational: MCP should work cleanly with normal HTTP infrastructure instead of requiring sticky sessions, shared session stores, or body-inspecting gateways. Remote MCP servers should be easier to load balance, route, cache, and observe.

The release candidate is available before the final specification so SDK maintainers and implementers can validate the changes against real workloads. The article explicitly says the release contains breaking changes.

### A Stateless Protocol

The headline change is that MCP becomes stateless at the protocol layer. In the earlier Streamable HTTP model, clients first initialized a session and then sent later requests with an `Mcp-Session-Id`. That model tied the client to a server instance or required infrastructure to coordinate session state.

In the release candidate, the old initialize and initialized exchange is removed. Protocol version, client details, and client capabilities are carried in request metadata. A new `server/discover` method lets a client fetch capabilities when it needs them before making calls.

The article stresses that removing protocol-level sessions does not force applications to avoid state. Instead, servers can return explicit handles from tools and require the model to pass those handles back in later calls. That makes state visible to the model and portable across server instances.

Server-to-client requests are also constrained. A server can ask the client for something only while it is processing a client-started request. For prompts or elicitation, the server can return an input-required result with enough state for the client to resume the original call after gathering answers. Because the state travels in the payload, the retried request can be handled by any instance.

### Routability, Caching, and Tracing

The HTTP transport requires headers such as `Mcp-Method` and `Mcp-Name` so gateways and load balancers can route based on operation without inspecting JSON request bodies. Servers must reject requests where headers and payload disagree.

List and resource-read responses can include cache metadata such as freshness duration and scope. This lets clients cache data such as tool lists without relying only on a long-lived event stream for invalidation.

The specification also documents W3C Trace Context propagation through request metadata. This is meant to make MCP calls visible inside distributed traces that pass from the host application through SDKs, servers, and downstream systems.

### Extensions

The article says extensions existed in the previous release, but did not yet have enough formal process. The new framework gives extensions reverse-DNS identifiers, capability negotiation, independent repositories, delegated maintainers, independent versioning, and a SEP path from experimental to official.

MCP Apps becomes an official extension. It allows servers to provide interactive HTML interfaces that hosts render inside sandboxed iframes. Tools declare UI templates ahead of time, and UI-triggered actions still go through the same JSON-RPC, audit, and consent paths as direct tool calls.

Tasks also becomes an official extension. It is moved out of the experimental core because production feedback showed enough redesign pressure. Under the new lifecycle, a server can return a task handle from a tool call, and clients interact with that task through task-specific methods. The list operation is removed because safe scoping is difficult without sessions.

### Authorization

Several SEPs harden MCP authorization around OAuth 2.0 and OpenID Connect deployment realities. Clients must validate issuer information in authorization responses, Dynamic Client Registration includes OpenID Connect application type, credentials are bound to the issuing authorization server, and the spec clarifies refresh-token requests, scope accumulation, and discovery URL behavior.

The motivation is that MCP clients often interact with many servers, which makes mix-up and issuer confusion especially important to handle correctly.

### Deprecations and Schema Changes

Roots, Sampling, and Logging are marked as deprecated under a new lifecycle policy. This does not remove them immediately. The article describes the deprecation as annotation-only for this release and says removal would require a separate SEP under the lifecycle policy.

Tool input and output schemas are upgraded to full JSON Schema 2020-12. Input schemas still require an object at the root, but they gain composition, conditionals, and references. Output schemas are no longer restricted to objects. Implementations should avoid automatically dereferencing external references and should limit schema depth and validation time.

The article also notes that the error code for missing resources changes from an MCP-specific code to the standard JSON-RPC invalid-params code.

### Governance and Timeline

The release contains breaking changes, but the authors position this as an exceptional foundational revision rather than a normal future pattern. Future evolution should rely more on extension tracks and a formal feature lifecycle with deprecation windows.

Standards Track SEPs must also have matching conformance-suite scenarios before reaching Final status. That links the governance process to executable validation and SDK tiering.

The release candidate was locked on 2026-05-21, and the final specification is planned for 2026-07-28. The article asks implementers to validate during that window and file issues in the specification repository when they find problems.
