import pytest
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_health_checks(client):
    for port_path in ["/health"]:
        resp = await client.get(port_path)
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_and_login(client):
    import uuid
    email = f"driver_{uuid.uuid4().hex[:8]}@test.com"
    resp = await client.post("/auth/register", json={
        "email": email,
        "password": "testpass123",
        "role": "driver",
        "plate_number": "FLOW-001",
    })
    assert resp.status_code in (200, 201)
    token = resp.json()["access_token"]
    assert token


@pytest.mark.asyncio
async def test_book_journey(client, auth_token):
    departure = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    resp = await client.post(
        "/bookings",
        json={
            "origin_lat": 53.3498,
            "origin_lng": -6.2603,
            "destination_lat": 51.8985,
            "destination_lng": -8.4756,
            "departure_time": departure,
            "plate_number": "TEST-001",
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code in (200, 201, 409)
