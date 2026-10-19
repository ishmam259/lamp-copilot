"""FastAPI entry point. All routes live under /api/v1."""

import importlib
import threading
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect

from app.api.routes import router
from app.config import registry_secret, settings
from app.db.models import Base
from app.db.seed import load_seed
from app.db.session import SessionLocal, engine, get_db
from app.engines import logbus, mailer

API_PREFIX = "/api/v1"


def _schema_is_current() -> bool:
    """True if every table and column of the models exists in the database."""
    insp = inspect(engine)
    for table in Base.metadata.sorted_tables:
        if not insp.has_table(table.name):
            return False
        if {c.name for c in table.columns} - {c["name"] for c in insp.get_columns(table.name)}:
            return False
    return True


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        registry_secret()  # refuse to start without a real REGISTRY_KEY (unless DEV_MODE)
        # Empty database, or one left by an older version of the app: (re)load the seed pharmacy.
        if not _schema_is_current():
            with SessionLocal() as db:
                load_seed(db)
    except Exception as exc:
        mailer.alert("startup", "[LaMP] API failed to start",
                     f"The API stopped during startup at {_now()}.\n\n{type(exc).__name__}: {exc}\n\n"
                     "Check the backend logs (docker compose logs backend) and restart it.", background=False)
        raise
    yield


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


app = FastAPI(title="LaMP-Copilot API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=API_PREFIX)


def _log_system_error(route: str, error: str, at: str, rid: str) -> None:
    gen = app.dependency_overrides.get(get_db, get_db)()  # the same database the routes use
    try:
        db = next(gen)
        logbus.log("T0", "SYSTEM", "system_error", db, route=route, error=error, at=at, request_id=rid)
        db.commit()
    except Exception:
        pass
    finally:
        gen.close()


@app.exception_handler(Exception)
async def crash_alert(request: Request, exc: Exception):
    """Any unhandled error: a plain 500 with a request id, a system_error log event, and an
    email to the admin (engines/mailer.py). No request data goes into the log or the email."""
    rid = uuid.uuid4().hex[:12]
    where = f"{request.method} {request.url.path}"
    frame = traceback.extract_tb(exc.__traceback__)[-1] if exc.__traceback__ else None
    at = f"{Path(frame.filename).name}:{frame.lineno} in {frame.name}" if frame else "unknown"
    # Email first; the log line goes on a background thread, since the database may be what failed.
    threading.Thread(target=_log_system_error, args=(where, type(exc).__name__, at, rid), daemon=True).start()
    mailer.alert(f"500 {where} {type(exc).__name__}", f"[LaMP] Server error on {where}",
                 f"The API hit an unexpected error and returned 500.\n\nRoute: {where}\nError: {type(exc).__name__}\n"
                 f"Where: {at}\nTime: {_now()}\nRequest id: {rid}\n\nThe same request id is in the audit log "
                 "(event system_error). Look at the backend logs and get back to it.")
    return JSONResponse({"detail": "Internal server error", "request_id": rid}, status_code=500)


# Pritom's chat router (POST /api/v1/chat), mounted once it exists.
try:
    app.include_router(importlib.import_module("app.agents.router").router, prefix=API_PREFIX)
except ImportError:
    pass
