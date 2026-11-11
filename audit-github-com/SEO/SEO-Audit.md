# SEO implementation notes

## Decision gate first
The current app is local-first; its private app routes are not the SEO target. Use SEO only for a separate public docs/marketing origin (e.g. `https://sentinel.example.org/`). Replace the placeholder domain before publishing. Do not index a localhost app or leak records through prerendering.

## Current confirmed state
- `index.html`: static title and description only; 11 SPA routes share one title.
- No canonical, OG/Twitter metadata, schema, robots/sitemap, manifest or favicon.
- Client-rendered SPA shell; crawlers initially receive only `#root`.
- `/robots.txt`, `/sitemap.xml` return SPA HTML with HTTP 200; unknown routes also return SPA 200 (soft-404).
- GitHub repo is public, has relevant description/topics, MIT licence, release v0.2.0; Pages disabled and no custom OG image.

## SEO priorities
1. Publish a distinct prerendered public site and docs; leave app local-only.
2. Add accurate titles/descriptions/canonicals/OG for public pages, not private app routes.
3. Serve actual robots and XML sitemap with correct content types and status.
4. Add SoftwareApplication and FAQ JSON-LD using only verifiable product facts; never add ratings/reviews unless real and substantiated.
5. Fix soft-404 behavior on app and public site.
6. Optimise banner/screenshots, add descriptive alt text, and link docs/release/security/support.

See `keyword-map.md`, `meta-templates.md`, `../Robots/`, `../Metadata/`, `../Schema/`.
