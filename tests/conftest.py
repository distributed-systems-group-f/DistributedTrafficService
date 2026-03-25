import pytest
import pytest_asyncio
import httpx


BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest_asyncio.fixture
async def auth_token(client):
    # Register a test user
    resp = await client.post("/auth/register", json={
        "email": "testdriver@example.com",
        "password": "testpassword123",
        "role": "driver",
        "plate_number": "TEST-001",
        "region": "EU_WEST_IRELAND",
    })
    if resp.status_code in (200, 201):
        return resp.json()["access_token"]
    # Login if already registered
    resp = await client.post("/auth/login", json={
        "email": "testdriver@example.com",
        "password": "testpassword123",
    })
    return resp.json()["access_token"]
