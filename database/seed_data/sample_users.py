"""
Seed sample users for testing.
Run via: python database/seed_data/sample_users.py
"""
import asyncio
import asyncpg
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USERS = [
    ("driver1@test.com", "password123", "driver", "IRL-001", "EU_WEST_IRELAND"),
    ("driver2@test.com", "password123", "driver", "UK-002", "EU_WEST_UK"),
    ("driver3@test.com", "password123", "driver", "FR-003", "EU_WEST_FRANCE"),
    ("enforcement1@test.com", "password123", "enforcement_agent", None, "EU_WEST_IRELAND"),
    ("admin@test.com", "password123", "admin", None, None),
]


async def seed():
    conn = await asyncpg.connect(
        "postgresql://traffic_admin:dev_password@localhost:5432/traffic_service"
    )
    try:
        for email, pw, role, plate, region in USERS:
            hashed = pwd_context.hash(pw)
            await conn.execute(
                """
                INSERT INTO auth.users (email, password_hash, role, plate_number, region)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (email) DO NOTHING
                """,
                email, hashed, role, plate, region,
            )
        print("Sample users seeded successfully.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
