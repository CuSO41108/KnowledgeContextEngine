from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse

from app.api import router
from app.db import Base, engine
from app import models  # noqa: F401
from app.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="engine-python", lifespan=lifespan)


@app.middleware("http")
async def require_internal_token(request: Request, call_next):
    token = settings.kce_internal_token.strip()
    if token and request.url.path.startswith("/internal/"):
        expected = f"Bearer {token}"
        if request.headers.get("Authorization", "") != expected:
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
    return await call_next(request)


app.include_router(router)
