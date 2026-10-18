"""FastAPI entry point. All routes live under /api/v1."""

import importlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from app.api.routes import router
from app.config import registry_secret, settings
from app.db.models import Base
from app.db.seed import load_seed
from app.db.session import SessionLocal, engine

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
    registry_secret()  # refuse to start without a real REGISTRY_KEY (unless DEV_MODE)
    # Empty database, or one left by an older version of the app: (re)load the seed pharmacy.
    if not _schema_is_current():
        with SessionLocal() as db:
            load_seed(db)
    yield


app = FastAPI(title="LaMP-Copilot API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=API_PREFIX)

# Pritom's chat router (POST /api/v1/chat), mounted once it exists.
try:
    app.include_router(importlib.import_module("app.agents.router").router, prefix=API_PREFIX)
except ImportError:
    pass
