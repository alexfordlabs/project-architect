---
template_name: WEB_SECURITY_HEADERS
generate_when: "conditional"
required_decisions:
  - project.type
optional_decisions:
  - stack.frontend.framework
  - stack.hosting.provider
  - stack.containerization
depends_on: []
revision_triggers:
  - stack.frontend.framework
  - stack.hosting.provider
---

# Web Security Headers — {{project_name}}

> HTTP response-header hardening for **{{project_name}}** ({{frontend_framework_or_web_app}}).
> Grounded in the [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/).
> Headers are a cheap, high-leverage defence-in-depth layer — they don't replace
> input validation, output encoding, or authn/z, but they close whole classes of
> browser-side attack (XSS, clickjacking, MIME-sniffing, mixed content, referrer
> leakage, cross-origin data theft).

## Where headers are set

{{where_headers_set}} — e.g. the framework's response middleware ({{frontend_framework}}),
a reverse proxy / CDN edge ({{hosting_provider}}), or both. Prefer setting them as
close to the origin as possible and assert them at the edge so a misconfigured app
can't silently drop them. Apply to **all** responses (including errors + redirects).

## Headers to ADD

| Header | Purpose | Recommended value (tune per app) |
|---|---|---|
| `Strict-Transport-Security` | Force HTTPS; prevent SSL-strip | `max-age=63072000; includeSubDomains` (append `; preload` only if you meet the [hstspreload.org](https://hstspreload.org) criteria — `{{hsts_preload}}`) |
| `Content-Security-Policy` | Mitigate XSS / injection / mixed content | `{{csp_policy}}` (start from `default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; upgrade-insecure-requests`) |
| `X-Content-Type-Options` | Block MIME-type sniffing | `nosniff` |
| `X-Frame-Options` | Legacy clickjacking defence (back-stops CSP `frame-ancestors`) | `DENY` |
| `X-Permitted-Cross-Domain-Policies` | Block Adobe Flash/PDF cross-domain policy loading | `none` |
| `Referrer-Policy` | Limit referrer leakage | `no-referrer` (or `strict-origin-when-cross-origin` if referrers are needed) |
| `Permissions-Policy` | Disable unused browser features/APIs | `{{permissions_policy}}` (default-deny: `accelerometer=(), camera=(), geolocation=(), microphone=(), payment=()`, …) |
| `Cross-Origin-Opener-Policy` | Isolate the browsing context from popups | `same-origin` |
| `Cross-Origin-Embedder-Policy` | Require explicit opt-in for cross-origin resources (needed for cross-origin isolation) | `require-corp` |
| `Cross-Origin-Resource-Policy` | Stop other origins embedding your resources | `same-origin` |
| `Cache-Control` (sensitive responses) | Keep auth'd/PII responses out of caches | `no-store, max-age=0` |
| `Clear-Site-Data` (logout endpoint) | Purge client state on logout | `"cache", "cookies", "storage"` |
| `X-DNS-Prefetch-Control` | Avoid prefetch-based leakage | `off` |

## Content-Security-Policy construction

CSP is the highest-value and the most app-specific header — build it deliberately:

1. Start from the strict baseline above; add only the sources **this app actually uses**.
2. Prefer **nonces or hashes** over `'unsafe-inline'`/`'unsafe-eval'`. Emit a per-request
   nonce (`script-src 'nonce-{{nonce}}'`) rather than allowlisting inline scripts.
3. Set `frame-ancestors` (CSP) AND `X-Frame-Options` (legacy) — CSP supersedes the latter
   but older browsers still honour it.
4. Roll out with `Content-Security-Policy-Report-Only` + a `report-to`/`report-uri`
   endpoint, watch violations for {{csp_observation_window}}, then enforce.
5. Re-audit the policy whenever a third-party script/domain is added.

This project's CSP directives: `{{csp_directives}}`.

## Headers to REMOVE (information disclosure)

Strip server/framework fingerprints so attackers can't target known CVEs:

- `Server`, `X-Powered-By`, `X-AspNet-Version` / `X-AspNetMvc-Version`, `X-Generator`,
  `X-Php-Version`, `X-SourceMap` / `SourceMap`, and any other `X-*-Version`/CMS banner.
- Configure {{hosting_provider_or_proxy}} to suppress or overwrite these.

## CORS (if this app exposes a cross-origin API)

- Validate the `Origin` header against a strict **allowlist** (exact, case-sensitive match);
  never reflect the request `Origin` back unconditionally.
- CORS is a browser-enforced control only — keep server-side authz regardless.
- Allowed origins: {{allowed_origins}}.

## Verification

- Scan with [securityheaders.com](https://securityheaders.com) and the OWASP Secure
  Headers Project checklist; target an **A** grade.
- Add a CI/integration test asserting the headers are present on a representative response
  (so a future refactor can't silently drop them).
- Re-verify after any CDN/proxy/framework upgrade.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
