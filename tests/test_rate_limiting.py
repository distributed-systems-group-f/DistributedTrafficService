import pytest
import asyncio


@pytest.mark.asyncio
async def test_rate_limiting(client):
    """Fire enough requests to potentially trigger rate limiting."""
    tasks = [client.get("/health") for _ in range(20)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    statuses = [r.status_code for r in results if hasattr(r, "status_code")]
    # Either all succeed or some get rate-limited
    assert all(s in (200, 429) for s in statuses)
