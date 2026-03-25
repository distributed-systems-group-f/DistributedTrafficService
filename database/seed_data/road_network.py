"""
Seed road segments for Ireland, UK, and France.
Run via: python database/seed_data/road_network.py
"""
import asyncio
import asyncpg

SEGMENTS = {
    "region_ireland": [
        ("Dublin-Cork", 53.3498, -6.2603, 51.8985, -8.4756, 150),
        ("Dublin-Galway", 53.3498, -6.2603, 53.2707, -9.0568, 120),
        ("Dublin-Limerick", 53.3498, -6.2603, 52.6638, -8.6267, 130),
        ("Dublin-Belfast", 53.3498, -6.2603, 54.5973, -5.9301, 180),
        ("Cork-Limerick", 51.8985, -8.4756, 52.6638, -8.6267, 100),
        ("Galway-Limerick", 53.2707, -9.0568, 52.6638, -8.6267, 80),
        ("Dublin-Waterford", 53.3498, -6.2603, 52.2593, -7.1101, 90),
        ("Cork-Waterford", 51.8985, -8.4756, 52.2593, -7.1101, 70),
        ("Galway-Sligo", 53.2707, -9.0568, 54.2766, -8.4761, 60),
        ("Dublin-Holyhead_Ferry", 53.3498, -6.2603, 53.3083, -4.6325, 200),
    ],
    "region_uk": [
        ("London-Birmingham", 51.5074, -0.1278, 52.4862, -1.8904, 200),
        ("London-Manchester", 51.5074, -0.1278, 53.4808, -2.2426, 180),
        ("London-Edinburgh", 51.5074, -0.1278, 55.9533, -3.1883, 150),
        ("Birmingham-Manchester", 52.4862, -1.8904, 53.4808, -2.2426, 160),
        ("Manchester-Leeds", 53.4808, -2.2426, 53.8008, -1.5491, 140),
        ("London-Bristol", 51.5074, -0.1278, 51.4545, -2.5879, 170),
        ("Bristol-Cardiff", 51.4545, -2.5879, 51.4816, -3.1791, 120),
        ("Edinburgh-Glasgow", 55.9533, -3.1883, 55.8642, -4.2518, 130),
        ("London-Dover", 51.5074, -0.1278, 51.1279, 1.3134, 160),
        ("Holyhead-Birmingham", 53.3083, -4.6325, 52.4862, -1.8904, 110),
    ],
    "region_france": [
        ("Paris-Lyon", 48.8566, 2.3522, 45.7640, 4.8357, 200),
        ("Paris-Marseille", 48.8566, 2.3522, 43.2965, 5.3698, 180),
        ("Paris-Bordeaux", 48.8566, 2.3522, 44.8378, -0.5792, 170),
        ("Paris-Lille", 48.8566, 2.3522, 50.6292, 3.0573, 190),
        ("Lyon-Marseille", 45.7640, 4.8357, 43.2965, 5.3698, 150),
        ("Bordeaux-Toulouse", 44.8378, -0.5792, 43.6047, 1.4442, 130),
        ("Paris-Calais", 48.8566, 2.3522, 50.9513, 1.8587, 160),
        ("Calais-Dunkirk", 50.9513, 1.8587, 51.0344, 2.3770, 120),
        ("Nice-Marseille", 43.7102, 7.2620, 43.2965, 5.3698, 140),
        ("Paris-Strasbourg", 48.8566, 2.3522, 48.5734, 7.7521, 160),
    ],
}


async def seed():
    conn = await asyncpg.connect(
        "postgresql://traffic_admin:dev_password@localhost:5432/traffic_service"
    )
    try:
        for schema, segments in SEGMENTS.items():
            for name, slat, slng, elat, elng, cap in segments:
                await conn.execute(
                    f"""
                    INSERT INTO {schema}.road_segments
                      (name, start_point_lat, start_point_lng, end_point_lat, end_point_lng, max_capacity_per_slot)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT DO NOTHING
                    """,
                    name, slat, slng, elat, elng, cap,
                )
        print("Road network seeded successfully.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
