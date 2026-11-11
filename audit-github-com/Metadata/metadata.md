# Public site metadata checklist

- [ ] Unique `<title>` (50–60 characters as a heuristic, not a hard rule) + useful description for every public page.
- [ ] Canonical uses one HTTPS origin; redirects normalize trailing slash/host.
- [ ] OG: `og:type=website`, `og:title`, `og:description`, `og:url`, `og:image` absolute URL; image 1200×630, alt text.
- [ ] Twitter card `summary_large_image` and matching fields.
- [ ] `lang="en-GB"`; theme-color consistent with visual system.
- [ ] Favicon SVG/PNG + apple-touch-icon + manifest; no broken asset paths.
- [ ] JSON-LD matches visible content and current release. No fake ratings/reviews.
- [ ] Sitemap contains canonical public URLs only. Robots file is plain text.
- [ ] Local app is `noindex` / disallowed from crawlers; this is not an access-control measure.
- [ ] Per-route title updates in SPA; SSR/prerender preferred for public content.
