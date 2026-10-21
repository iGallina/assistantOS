# Technical Design: The Page Refuses Other Websites

**PRD:** [page-refuses-other-websites-prd.md](page-refuses-other-websites-prd.md)

## Overview

One guard in front of every request the page server answers. It checks three things the browser sends or obeys and
that a website cannot forge or switch off from inside the owner's browser: the address the request was sent to
(`Host`), the website that sent it (`Origin`), and whether the response may be framed. Same-origin rules, which the
browser already enforces, keep covering cross-site reads; the `Host` check closes the one way around them (DNS
rebinding). The page's own HTML and JavaScript do not change.

## Existing Code

- **Posture: Preserve.** The page runs in production installs; its routes, payloads and behavior stay as they are.
- Reused: the page server's single request handler; the guard runs before its routing.
- Kept: the server listens on `127.0.0.1` only (Out of Scope: other devices). It never sends
  `Access-Control-Allow-Origin` or answers `OPTIONS`; both stay that way, since either would hand other websites the
  reads and writes this change takes away.

## Architecture

- **Workload:** the existing local stdlib HTTP server (`aos page`), started at logon by the `assistantOS-pagina` task.
- **Data store / dependencies:** none added.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| What "the page itself" is | The origins `http://127.0.0.1:<port>` and `http://localhost:<port>`, where `<port>` is the port the server actually bound | Covers every entry point in AC-ORIGIN-03: the shortcut, the installer link and Fizzy's `page_url` all use `127.0.0.1:8422`; typing `localhost` is the one other spelling. Using the bound port makes `aos page --port N` work with no setting |
| DNS rebinding (AC-ORIGIN-01, AC-ORIGIN-02) | Every request, read or write, is refused unless its `Host` header is one of the two `host:port` values above (host compared case-insensitively). A missing `Host` is refused | After rebinding, the browser still sends the attacker's host name in `Host`; it is the one signal a rebinding page cannot change. Checking reads as well as writes is what keeps the conversations unreadable |
| Writes from other websites (AC-ORIGIN-01) | Every `POST` is refused unless its `Origin` header is one of the two page origins. A missing `Origin` is refused | Every current browser sends `Origin` on a `fetch` POST, same-origin included, and a page cannot suppress or forge it. Today the server parses any body as JSON whatever its content type, so a plain form or `no-cors` post works; the `Origin` check closes that without relying on content types. Non-browser callers that omit `Origin` are out of scope (PRD) and none exists: Hermes uses `aos mcp` |
| Framing (AC-ORIGIN-04) | Every response carries `Content-Security-Policy: frame-ancestors 'none'` and `X-Frame-Options: DENY` | `frame-ancestors` is the standard; `X-Frame-Options` covers browsers that ignore it. Both are headers only, no page change |
| JSON read by inclusion (AC-ORIGIN-02) | Every response carries `X-Content-Type-Options: nosniff` | Stops a site loading `/api/state` or `/api/events` as a script or style; the browser then blocks the cross-site JSON outright. One header |
| What a refusal looks like | `403`, JSON body `{"error": "forbidden"}`, nothing read from or written to the store, no line in `errors.log` | The page itself never sees a refusal, so there is no owner-facing text to translate. Logging every probe from a website would let any site fill the owner's log |
| Reaching installs that already run | `aos update` ends by restarting the page task on Windows (`assistantOS-pagina`) | The page process keeps running the old code until the next logon; without the restart an updated install stays open to other websites until a reboot |
| Where the check lives | In the request handler, before routing, for every method the server answers | One place: the setup screens of the first-run PRD are added to the same server and inherit it (AC-SETUP-08 of `docs/prds/first-run-without-terminal/`) |

## Interfaces

No route, request or response body changes. The behavior every route gets:

```
Any request
  Host not in {127.0.0.1:<port>, localhost:<port>}       → 403 {"error": "forbidden"}
POST
  Origin not in {http://127.0.0.1:<port>, http://localhost:<port>} → 403 {"error": "forbidden"}
Every response (including 403 and 404)
  Content-Security-Policy: frame-ancestors 'none'
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
```

## Testing

- Unit tests against a real server on a free port: each route (`/`, `/api/state`, `/api/events`, `/api/mark`,
  `/api/ask`) with the allowed `Host` and `Origin` pairs succeeds; with a foreign `Host` (`evil.example:<port>`),
  a foreign `Origin`, a missing `Origin` on `POST`, or `Origin: null`, it returns 403 and the store is unchanged
  (no mark, no queued request). The three headers are on every response.
- Manual, once, in the Windows VM with Edge: the four ways of opening the page in AC-ORIGIN-03 load and every button
  works; `--port 8500` with both spellings works too.

## Open Questions

None. Browsers' own "allow access to local network" prompts are left as they are: this change does not depend on them.
