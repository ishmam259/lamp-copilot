"""FastAPI entry point. All routes live under /api/v1."""

import importlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from app.api.routes import router
from app.config import settings
from app.db.seed import load_seed
from app.db.session import SessionLocal, engine

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_: FastAPI):
    # First start on an empty database: load the seed pharmacy.
    if not inspect(engine).has_table("pharmacy"):
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
