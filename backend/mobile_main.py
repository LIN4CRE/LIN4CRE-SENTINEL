"""Separate, read-only ASGI application for the Android companion.

Run behind a trusted HTTPS/VPN endpoint. This app exposes no core mutations,
assistant operations, recovery, host companion, static frontend, or API docs.
"""
from fastapi import FastAPI, Request

from .db import initialise
from .mobile_api import router

initialise()
app = FastAPI(title="SENTINEL Mobile Read-only API", version="0.1.0", docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(router)


@app.middleware("http")
async def mobile_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), usb=()")
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ready"}
