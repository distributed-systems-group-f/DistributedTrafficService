import httpx
from fastapi import APIRouter, Request, Response, HTTPException
from shared.config import get_settings

router = APIRouter()
settings = get_settings()

SERVICE_MAP = {
    "/auth": settings.auth_service_url,
    "/bookings": settings.booking_service_url,
    "/verify": settings.verification_service_url,
    "/notifications": settings.notification_service_url,
    "/analytics": settings.analytics_service_url,
}


async def proxy(request: Request, target_url: str) -> Response:
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = target_url + request.url.path + (
            f"?{request.url.query}" if request.url.query else ""
        )
        body = await request.body()
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=body,
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers),
                media_type=resp.headers.get("content-type"),
            )
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {target_url}")


@router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_auth(request: Request, path: str):
    return await proxy(request, settings.auth_service_url)


@router.api_route("/bookings/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_bookings(request: Request, path: str):
    return await proxy(request, settings.booking_service_url)


@router.api_route("/verify/{path:path}", methods=["GET", "POST"])
async def proxy_verify(request: Request, path: str):
    return await proxy(request, settings.verification_service_url)


@router.api_route("/notifications/{path:path}", methods=["GET", "POST"])
async def proxy_notifications(request: Request, path: str):
    return await proxy(request, settings.notification_service_url)


@router.api_route("/analytics/{path:path}", methods=["GET", "POST"])
async def proxy_analytics(request: Request, path: str):
    return await proxy(request, settings.analytics_service_url)
