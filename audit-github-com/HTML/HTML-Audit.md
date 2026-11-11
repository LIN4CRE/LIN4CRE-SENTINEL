# HTML / document-shell Audit

- `index.html` has `lang="en"`, UTF-8, viewport, theme-color, title and description — good baseline.
- No canonical/OG/Twitter/manifest/icon/JSON-LD/robots meta.
- SPA root is empty `<div id="root">`; no meaningful no-JS content. This is acceptable for local tool operation but poor for public SEO.
- `<main>` exists in `Layout`, but no skip-link and route focus management.
- `robots.txt`/`sitemap.xml` are swallowed by SPA fallback and return HTML 200.
- Unknown route returns 200 SPA shell; `HEAD` returns 405.
- For a public site, prerender/SSR the public pages separately. Do not prerender user records or app state.

See `snippets.md` for shell, 404, and `<head>` template.
