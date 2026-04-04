import httpx
from fastapi import APIRouter, Request, Response, HTTPException
from shared.config import get_settings

router = APIRouter()
settings = get_settings()


async def proxy(request: Request, target_url: str) -> Response:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        url = target_url + request.url.path + (
            f"?{request.url.query}" if request.url.query else ""
        )
        body = await request.body()
        try:
            request_headers = {
                k: v
                for k, v in request.headers.items()
                if k.lower() not in {"host", "connection", "content-length"}
            }
            resp = await client.request(
                method=request.method,
                url=url,
                headers=request_headers,
                content=body,
            )
            response_headers = {
                k: v
                for k, v in resp.headers.items()
                if k.lower() not in {"connection", "transfer-encoding"}
            }
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=response_headers,
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


@router.api_route("/bookings", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_bookings_root(request: Request):
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