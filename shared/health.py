from fastapi import APIRouter
from datetime import datetime


def create_health_router(service_name: str) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": service_name,
            "timestamp": datetime.utcnow().isoformat(),
        }

    return router
