# CSS Audit

- Main styles are `src/styles.css` (656 lines) and `src/operations.css` (282 lines); tokens exist, responsive breakpoints range 430–1500 px.
- Good: focus-visible styling, CSS variables, grid collapse, off-canvas sidebar, consistent border/radius system.
- Confirmed issue: 7–10 px font sizes are widespread; secondary contrast fails; no reduced-motion/forced-colors rules; all sizes primarily in px.
- Proposed patch: `fixes.css` (contrast/type/motion/target size). It is a starter override; replace ad-hoc values with semantic tokens and verify each actual contrast pair. Do not blindly override `--text-muted` if the existing variable semantics differ.
