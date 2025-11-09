from fastapi import FastAPI
from app.api import stream
from app.core import settings

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION
)

app.include_router(stream.router)