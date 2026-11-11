# Defensive security header examples

Examples only. Roll out CSP as `Report-Only` first and inspect actual violations; do not paste blindly into the app because allowed resources can differ by build/host. HSTS is for HTTPS public origins only.

## FastAPI middleware sketch

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), usb=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        # Add HSTS only behind a correctly configured HTTPS public origin.
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Start with report-only; replace with Content-Security-Policy after validating reports.
        response.headers.setdefault(
            "Content-Security-Policy-Report-Only",
            "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
            "form-action 'self'; img-src 'self' data:; font-src 'self'; "
            "style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self' http://127.0.0.1:8765"
        )
        return response
```

- Adjust `connect-src` to the exact host-companion origin/proxy configuration in the shipped build; do not use `*`.
- If Vite injects inline styles/scripts, prefer nonces/hashes or refactor before enforcing a strict CSP. Avoid adding `'unsafe-eval'`.
- Reverse proxy should terminate TLS, redirect HTTP→HTTPS for public site, set HSTS only once all subdomains support HTTPS.
- `X-Frame-Options: DENY` is appropriate for app pages that never need framing; retain `SAMEORIGIN` if a documented same-origin embed exists.

## Static cache policy

```text
/assets/<content-hash>.*  Cache-Control: public, max-age=31536000, immutable
/index.html               Cache-Control: no-cache
/api/*                    Cache-Control: no-store
```
