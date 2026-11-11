from __future__ import annotations

import asyncio
import json
import os
import uuid

from .db import audit, connect, settings, transaction, utcnow


async def monitor_loop() -> None:
    """Periodic real inspection. No updates or repairs are performed by the monitor."""
    if os.getenv("SENTINEL_DISABLE_MONITOR") == "1":
        return
    await asyncio.sleep(15)
    while True:
        try:
            from .operations import inspection
            with connect() as conn:
                current = settings(conn)
            if current.get("automatic_monitoring", True):
                run_id = str(uuid.uuid4())
                with transaction() as conn:
                    conn.execute("INSERT INTO monitor_runs(id,started_at,status) VALUES(?,?,?)", (run_id, utcnow(), "running"))
                try:
                    result = await inspection()
                    status = "succeeded" if result["host"]["connected"] else "partial"
                    summary = {"host_connected": result["host"]["connected"], "host_error": result["host"]["error"], "core_checks": result["core"]["checks"]}
                except Exception as exc:
                    status = "failed"
                    summary = {"error": f"{type(exc).__name__}: {exc}"}
                with transaction() as conn:
                    conn.execute("UPDATE monitor_runs SET finished_at=?,status=?,summary_json=? WHERE id=?", (utcnow(), status, json.dumps(summary), run_id))
                    conn.execute("INSERT INTO settings(key,value_json) VALUES('last_monitor_run',?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json", (json.dumps(utcnow()),))
                    audit(conn, "monitor.completed", "system", run_id, f"Automatic health monitor {status}", summary)
                interval = int(current.get("monitor_interval_minutes", 60))
            else:
                interval = 5
            await asyncio.sleep(max(5, min(interval, 1440)) * 60)
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(300)
