# Accessibility fixes — implementation patterns

## 1. Skip link + main target

```tsx
// In Layout, before sidebar/topbar:
<a className="skip-link" href="#main-content">Skip to main content</a>
// Main:
<main id="main-content" className="main-content" tabIndex={-1}>{children}</main>
```

```css
.skip-link { position: fixed; z-index: 10000; top: 8px; left: 8px; transform: translateY(-160%); padding: 12px 16px; background: #f2f7f3; color: #101713; border-radius: 8px; font-size: 16px; }
.skip-link:focus { transform: translateY(0); }
```

## 2. Modal focus trap

Prefer a maintained dialog primitive (`@radix-ui/react-dialog` or equivalent). If keeping the custom modal, implement initial focus, Tab loop, focus restoration, `aria-labelledby`, and make app shell inert while modal is open. The following is an outline, not a substitute for cross-browser testing:

```tsx
<section role="dialog" aria-modal="true" aria-labelledby="dialog-title" ref={dialogRef}>
  <h2 id="dialog-title">{title}</h2>
  {children}
</section>
```

- On open: store `document.activeElement`, focus first enabled control (or dialog with `tabIndex={-1}`).
- On Tab: cycle between visible enabled focusables; if none, keep focus on dialog.
- On Escape: close; on cleanup restore focus if still connected.
- Make non-dialog application root `inert` while open; restore previous value.

## 3. Toast live regions

```tsx
<div className="toast-stack" aria-live="polite" aria-relevant="additions text">
  {toasts.map(toast => <div key={toast.id} role={toast.tone === 'error' ? 'alert' : 'status'}>
    <span>{toast.message}</span>
    <button aria-label="Dismiss notification" onClick={dismiss}>...</button>
  </div>)}
</div>
```
Avoid applying both assertive alert and polite live region to the same node if a screen-reader test causes duplicate announcements; test actual AT/browser pairs.

## 4. Inline form error association

```tsx
<label htmlFor="programme-url">Programme URL</label>
<input id="programme-url" aria-invalid={Boolean(errors.programme_url)}
  aria-describedby={errors.programme_url ? 'programme-url-error' : 'programme-url-help'} />
<p id="programme-url-help">Use the canonical programme page.</p>
{errors.programme_url && <p id="programme-url-error" role="alert">{errors.programme_url}</p>}
```
On submit failure, focus the first invalid control and retain all entered values. Provide a form-level error summary if multiple fields fail.

## 5. Route focus & active navigation

After a client-side route change, move focus to the page H1 or `main` (without causing unwanted scroll); set `aria-current="page"` on exactly one active link. Respect reduced motion for any scroll behavior.

## 6. UI states and forms checklist

- Label each input; placeholder is never the sole label.
- Connect hints and errors with `aria-describedby`.
- Use `aria-busy="true"` for async regions and announce completion once.
- Add `aria-expanded`/`aria-controls` to disclosure buttons.
- Use 24×24 CSS px minimum target size; separate adjacent controls by at least 8 px.
- Do not rely on color alone for status or severity.
- Do not announce every keystroke or every polling update.
