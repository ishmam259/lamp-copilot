"""FastAPI entry point. All routes live under /api/v1."""

import importlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

API_PREFIX = "/api/v1"

app = FastAPI(title="LaMP-Copilot API", version="0.1.0")
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
