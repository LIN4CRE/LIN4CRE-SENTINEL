# JavaScript / React Audit

- React 19 + React Router 7.1.5 + Vite 6 + TypeScript strict; production build passes.
- All 11 route components load in one 425 KB JS chunk; no `React.lazy` observed.
- `DataContext` starts 10 parallel requests; one rejection can cause full-screen error; no timeout/AbortController.
- Assistant/Maintenance polling every 2.5s/3s; no hidden-tab pause/backoff.
- No XSS sinks found (`dangerouslySetInnerHTML`, `innerHTML`, `eval` absent); React escapes user text; Markdown is shown as `<pre>`.
- API state is honestly reported; kill switch and approval workflows are explicit.
- Proposed helpers in `fixes.ts` are patterns only; wire into current `api.ts`/`DataContext.tsx` and test network failures.
