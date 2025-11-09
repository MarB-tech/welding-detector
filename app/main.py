from fastapi import FastAPI
from app.api import stream

app = FastAPI(title="Welding Detector API")

app.include_router(stream.router)