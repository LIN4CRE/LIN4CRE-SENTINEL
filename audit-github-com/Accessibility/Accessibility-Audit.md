# Accessibility Audit — WCAG 2.2 AA target

**Score: 58/100.** Source-based audit; no NVDA/VoiceOver session was available. Confirmed measurements and specific patches are in `fixes.md` and `../CSS/fixes.css`.

## Confirmed strengths
- Semantic `<nav>`, `<main>`, `<header>`, `<footer>`, real buttons/links, one H1 per main page.
- Shared `Field` wraps label and input; `:focus-visible` style exists; decorative logo SVG is hidden from AT.
- Status generally has textual labels, not colour alone; contrast for primary text/accent passes AA.

## Confirmed issues
1. ~140 font-size declarations below 12 px, including 7–10 px. Raise microcopy floor and test 200% zoom.
2. Contrast failures: footer 2.96:1, nav section 3.44:1, placeholder 3.76:1, status small text ~3.2:1.
3. No skip link; route changes do not move focus to main heading.
4. Modal supports Escape but no focus trap/return, no `aria-labelledby`, no inert background.
5. Toasts lack live-region semantics; dismiss button lacks accessible name.
6. Field errors are toast-only; no `aria-invalid`/`aria-describedby` mapping.
7. No reduced-motion handling; 24×24 target-size misses on small controls; no `aria-current` on nav.

## Suggested verification before release
- axe-core on all 11 routes (empty, populated, loading, error states).
- Keyboard-only: open/close mobile drawer, modal, dropdown, filters, operation actions, skip link.
- NVDA + Firefox/Chrome and VoiceOver + Safari smoke tests.
- 200% zoom and 320 CSS px reflow; no horizontal page scroll (tables may use a labelled scroll region).
- High contrast / forced-colors and reduced-motion enabled.
- Test server-denied, offline, invalid form, expired approval, and failed restore states.
