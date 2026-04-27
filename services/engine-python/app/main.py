from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router
from app.db import Base, engine
from app import models  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="engine-python", lifespan=lifespan)
app.include_router(router)
