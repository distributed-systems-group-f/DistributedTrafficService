import pytest


@pytest.mark.asyncio
async def test_gateway_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    resp = await client.get(
        "/bookings/nonexistent-id",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code in (401, 422)


@pytest.mark.asyncio
async def test_missing_auth_rejected(client):
    resp = await client.get("/bookings/some-id")
    assert resp.status_code in (401, 403, 422)
