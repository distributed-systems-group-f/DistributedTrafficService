import pytest
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_cross_region_booking(client, auth_token):
    """Book a journey that crosses from Ireland into UK (cross-border segment)."""
    departure = (datetime.utcnow() + timedelta(hours=2)).isoformat()
    resp = await client.post(
        "/bookings",
        json={
            "origin_lat": 53.3498,  # Dublin
            "origin_lng": -6.2603,
            "destination_lat": 52.4862,  # Birmingham
            "destination_lng": -1.8904,
            "departure_time": departure,
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code in (200, 201, 409)
    if resp.status_code in (200, 201):
        data = resp.json()
        assert data["status"] in ("CONFIRMED", "REJECTED", "SAGA_IN_PROGRESS")
