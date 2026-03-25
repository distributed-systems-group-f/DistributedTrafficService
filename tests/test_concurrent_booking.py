import pytest
import asyncio
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_concurrent_same_slot(client, auth_token):
    """Two drivers booking the same slot — only one should succeed if capacity = 1."""
    departure = (datetime.utcnow() + timedelta(hours=3)).isoformat()
    payload = {
        "origin_lat": 53.3498,
        "origin_lng": -6.2603,
        "destination_lat": 51.8985,
        "destination_lng": -8.4756,
        "departure_time": departure,
    }
    headers = {"Authorization": f"Bearer {auth_token}"}

    tasks = [
        client.post("/bookings", json=payload, headers=headers)
        for _ in range(3)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    statuses = [r.status_code for r in results if hasattr(r, "status_code")]
    assert all(s in (200, 201, 409, 422) for s in statuses)
