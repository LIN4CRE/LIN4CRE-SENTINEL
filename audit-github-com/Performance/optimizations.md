# Performance implementation snippets

## 1. Lazy-load routes

```tsx
import { lazy, Suspense } from 'react'
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Assistant = lazy(() => import('./pages/Assistant'))
const Opportunities = lazy(() => import('./pages/Opportunities'))
// Apply to each route component.

<Suspense fallback={<div role="status" aria-live="polite">Loading page…</div>}>
  <Routes>{/* route elements */}</Routes>
</Suspense>
```

Prefer route-level lazy loading so an exception in an optional page does not block the whole app; add an error boundary with “Retry” if a chunk fails.

## 2. Vite manual chunks and budget

```ts
// vite.config.ts (adapt to existing config)
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react')) return 'react-vendor'
          if (id.includes('node_modules/react-router')) return 'router-vendor'
          if (id.includes('node_modules/lucide-react')) return 'icons-vendor'
        }
      }
    }
  }
})
```

Chunking alone may not reduce total transfer; lazy routes are the key first-load change. Add a CI bundle report and an initial-entry budget, not a total asset budget that blocks legitimate pages.

## 3. Static caching / compression

- Immutable one-year cache only for content-hashed files under `/assets/`.
- `index.html`: `no-cache` / revalidate.
- `/api/*`: `no-store` (contains user data).
- Enable gzip or Brotli at Caddy/Nginx/hosting edge for JS/CSS/JSON/SVG. Do not double-compress.

## 4. Data loading

- Use `Promise.allSettled` to render independent panels where safe.
- Keep safety-critical state (approvals, kill-switch, operation status) clearly marked stale if a refresh fails.
- Add `AbortController` + timeout and retry only idempotent GETs with bounded exponential backoff.
- Pause polling while `document.visibilityState === 'hidden'`; refresh on visibility return.
- Consider a `/api/bootstrap` endpoint only if it preserves authorization/partial failure and avoids duplicating business rules.

## 5. Images and fonts

- Resize banner to a 1200×630 social image; provide a smaller README image and a WebP/AVIF variant where GitHub supports it.
- Add intrinsic `width`/`height`, `loading="lazy"`, `decoding="async"` for below-fold screenshots.
- If brand requires Inter, self-host WOFF2 with `font-display: swap`; otherwise remove the unused Inter label and rely on system UI font.
