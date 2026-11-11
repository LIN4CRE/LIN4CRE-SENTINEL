# Robots & sitemap

- `robots.txt` is a **public marketing/docs site** template. Replace `sentinel.example.org` with the chosen canonical host; do not copy into local-app deployment.
- `robots-local.txt` is a conservative local-app variant. It is not a security control: authentication and loopback binding are still required.
- Current confirmed defect: local `/robots.txt` returns SPA HTML (200). Ensure static file routing occurs before SPA fallback and test `Content-Type: text/plain`.
- Keep user records, API paths and private app routes off public sitemaps. A robots disallow does not prevent access or guarantee deindexing.

Minimal public sitemap (generate from actual public pages; update `lastmod` only when content changes):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://sentinel.example.org/</loc></url>
  <url><loc>https://sentinel.example.org/features/</loc></url>
  <url><loc>https://sentinel.example.org/how-it-works/</loc></url>
  <url><loc>https://sentinel.example.org/downloads/</loc></url>
  <url><loc>https://sentinel.example.org/docs/</loc></url>
  <url><loc>https://sentinel.example.org/security/</loc></url>
  <url><loc>https://sentinel.example.org/accessibility/</loc></url>
  <url><loc>https://sentinel.example.org/support/</loc></url>
  <url><loc>https://sentinel.example.org/changelog/</loc></url>
</urlset>
```
