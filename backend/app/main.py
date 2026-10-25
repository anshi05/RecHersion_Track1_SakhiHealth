"""FastAPI app: CORS, error handler, routers, /api/health."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel

from app.api import analyze, explain, logs, measurements, personas, profile, report, timeline
from app.config import get_settings
from app.db import engine
from app.errors import AppError
from app.models import tables  # noqa: F401  (registers tables)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(title="Sakhi Health", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "llm": "live" if get_settings().llm_live else "fallback"}


for _r in (
    analyze.router, personas.router, profile.router, logs.router, measurements.router,
    timeline.router, explain.router, report.router,
):
    app.include_router(_r)
