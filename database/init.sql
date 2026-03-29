-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Regional schemas (simulate geo-partitioned databases)
CREATE SCHEMA IF NOT EXISTS region_ireland;
CREATE SCHEMA IF NOT EXISTS region_uk;
CREATE SCHEMA IF NOT EXISTS region_france;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS analytics;

-- ============================================================
-- IRELAND
-- ============================================================
CREATE TABLE IF NOT EXISTS region_ireland.road_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    start_point_lat DOUBLE PRECISION,
    start_point_lng DOUBLE PRECISION,
    end_point_lat DOUBLE PRECISION,
    end_point_lng DOUBLE PRECISION,
    max_capacity_per_slot INTEGER NOT NULL DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS region_ireland.reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL,
    segment_id UUID REFERENCES region_ireland.road_segments(id),
    driver_id UUID NOT NULL,
    time_slot_start TIMESTAMP NOT NULL,
    time_slot_end TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- UK
-- ============================================================
CREATE TABLE IF NOT EXISTS region_uk.road_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    start_point_lat DOUBLE PRECISION,
    start_point_lng DOUBLE PRECISION,
    end_point_lat DOUBLE PRECISION,
    end_point_lng DOUBLE PRECISION,
    max_capacity_per_slot INTEGER NOT NULL DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS region_uk.reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL,
    segment_id UUID REFERENCES region_uk.road_segments(id),
    driver_id UUID NOT NULL,
    time_slot_start TIMESTAMP NOT NULL,
    time_slot_end TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- FRANCE
-- ============================================================
CREATE TABLE IF NOT EXISTS region_france.road_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    start_point_lat DOUBLE PRECISION,
    start_point_lng DOUBLE PRECISION,
    end_point_lat DOUBLE PRECISION,
    end_point_lng DOUBLE PRECISION,
    max_capacity_per_slot INTEGER NOT NULL DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS region_france.reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL,
    segment_id UUID REFERENCES region_france.road_segments(id),
    driver_id UUID NOT NULL,
    time_slot_start TIMESTAMP NOT NULL,
    time_slot_end TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SEED: default road segments used by the saga route resolver
-- These IDs are deterministic (uuid5 of the region name) so the
-- booking saga can reference them via foreign key.
-- ============================================================
INSERT INTO region_ireland.road_segments (id, name, start_point_lat, start_point_lng, end_point_lat, end_point_lng, max_capacity_per_slot)
VALUES ('c8476fce-4136-5a82-a985-be50e80de41d', 'Ireland-Default', 53.3498, -6.2603, 51.8985, -8.4756, 150)
ON CONFLICT DO NOTHING;

INSERT INTO region_uk.road_segments (id, name, start_point_lat, start_point_lng, end_point_lat, end_point_lng, max_capacity_per_slot)
VALUES ('5ab73b95-6aa1-56a2-bede-05c0ecf43a7a', 'UK-Default', 51.5074, -0.1278, 53.4808, -2.2426, 200)
ON CONFLICT DO NOTHING;

INSERT INTO region_france.road_segments (id, name, start_point_lat, start_point_lng, end_point_lat, end_point_lng, max_capacity_per_slot)
VALUES ('0dfcd849-f0b8-5213-b721-44b067f63dd3', 'France-Default', 48.8566, 2.3522, 45.7640, 4.8357, 200)
ON CONFLICT DO NOTHING;

-- ============================================================
-- AUTH
-- ============================================================
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'driver',
    plate_number VARCHAR(20),
    region VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ANALYTICS
-- ============================================================
CREATE TABLE IF NOT EXISTS analytics.booking_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL,
    driver_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    region VARCHAR(50),
    segment_id UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- BOOKINGS (global)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL,
    origin_lat DOUBLE PRECISION,
    origin_lng DOUBLE PRECISION,
    destination_lat DOUBLE PRECISION,
    destination_lng DOUBLE PRECISION,
    departure_time TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    estimated_duration_minutes INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.segment_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID REFERENCES public.bookings(id),
    segment_id UUID NOT NULL,
    region VARCHAR(50) NOT NULL,
    time_slot_start TIMESTAMP NOT NULL,
    time_slot_end TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW()
);
