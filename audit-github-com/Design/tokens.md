# Proposed accessible design tokens

Use as a migration target; compare against existing tokens and apply incrementally.

```css
:root {
  color-scheme: dark;
  --color-bg: #0a0f0e;
  --color-panel: #111917;
  --color-panel-raised: #16211c;
  --color-border: #2b3932;
  --color-text: #e8efeb;
  --color-text-muted: #a0ada4;
  --color-text-subtle: #8f9c93;
  --color-accent: #b7ef72;
  --color-success: #7dd9a4;
  --color-warning: #f4c56a;
  --color-danger: #ff8b82;
  --font-ui: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Consolas, monospace;
  --text-xs: 0.75rem;  /* 12 px minimum */
  --text-sm: 0.875rem; /* 14 px */
  --text-md: 1rem;     /* 16 px */
  --text-lg: 1.25rem;
  --text-xl: 1.5rem;
  --text-2xl: clamp(1.75rem, 2.5vw, 2.25rem);
  --space-1: 0.25rem; --space-2: 0.5rem; --space-3: 0.75rem;
  --space-4: 1rem; --space-6: 1.5rem; --space-8: 2rem;
  --radius-sm: 0.5rem; --radius-md: 0.8rem; --radius-lg: 1rem;
}
```

Verify actual contrast pairs with a WCAG calculator after mapping each token to a rendered surface; do not assume token contrast is valid on every background.
