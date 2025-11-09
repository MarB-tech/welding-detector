from fastapi import FastAPI
from app.api import router as api_router
from app.core.config import settings

app = FastAPI(title="Welding Vision API")

# Rejestracja endpointów
app.include_router(api_router)

@app.get("/")
def root():
    return {"status": "running", "camera_url": settings.CAMERA_SERVER_URL}