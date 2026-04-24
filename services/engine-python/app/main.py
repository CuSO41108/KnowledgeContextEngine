from fastapi import FastAPI

from app.api import router

app = FastAPI(title="engine-python")
app.include_router(router)
