import sys
sys.path.insert(0, "/app")

from fastapi import FastAPI
from shared.health import create_health_router
from routes import router

app = FastAPI(title="Verification Service", version="1.0.0")

app.include_router(create_health_router("verification_service"))
app.include_router(router, prefix="/verify")
