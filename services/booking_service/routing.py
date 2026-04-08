import heapq
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import RouteNotFoundError


REGION_SCHEMA_MAP = {
    "EU_WEST_IRELAND": "region_ireland",
    "EU_WEST_UK": "region_uk",
    "EU_WEST_FRANCE": "region_france",
}

AVERAGE_SPEED_KMPH = 90.0
MIN_SEGMENT_MINUTES = 5


@dataclass(frozen=True)
class SegmentEdge:
    segment_id: str
    region: str
    schema: str
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    distance_km: float


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _to_minutes(distance_km: float) -> int:
    return max(MIN_SEGMENT_MINUTES, int(round((distance_km / AVERAGE_SPEED_KMPH) * 60)))


def _node_key(lat: float, lng: float) -> tuple[float, float]:
    # Endpoints in seed data share exact coordinates; rounding avoids floating-point drift.
    return (round(lat, 4), round(lng, 4))


async def _load_edges(db: AsyncSession) -> list[SegmentEdge]:
    edges: list[SegmentEdge] = []
    for region, schema in REGION_SCHEMA_MAP.items():
        rows = await db.execute(
            text(
                f"""
                SELECT
                    id::text AS id,
                    start_point_lat,
                    start_point_lng,
                    end_point_lat,
                    end_point_lng
                FROM {schema}.road_segments
                """
            )
        )
        for row in rows.mappings().all():
            slat = float(row["start_point_lat"])
            slng = float(row["start_point_lng"])
            elat = float(row["end_point_lat"])
            elng = float(row["end_point_lng"])
            edges.append(
                SegmentEdge(
                    segment_id=row["id"],
                    region=region,
                    schema=schema,
                    start_lat=slat,
                    start_lng=slng,
                    end_lat=elat,
                    end_lng=elng,
                    distance_km=_haversine_km(slat, slng, elat, elng),
                )
            )
    return edges


def _build_graph(
    edges: list[SegmentEdge],
) -> tuple[
    dict[tuple[float, float], list[tuple[tuple[float, float], SegmentEdge]]],
    dict[tuple[float, float], tuple[float, float]],
]:
    graph: dict[tuple[float, float], list[tuple[tuple[float, float], SegmentEdge]]] = {}
    node_positions: dict[tuple[float, float], tuple[float, float]] = {}

    for edge in edges:
        a = _node_key(edge.start_lat, edge.start_lng)
        b = _node_key(edge.end_lat, edge.end_lng)

        node_positions[a] = (edge.start_lat, edge.start_lng)
        node_positions[b] = (edge.end_lat, edge.end_lng)

        graph.setdefault(a, []).append((b, edge))
        graph.setdefault(b, []).append((a, edge))

    return graph, node_positions


def _nearest_node(
    lat: float,
    lng: float,
    node_positions: dict[tuple[float, float], tuple[float, float]],
) -> tuple[float, float]:
    return min(
        node_positions.keys(),
        key=lambda n: _haversine_km(lat, lng, node_positions[n][0], node_positions[n][1]),
    )


def _shortest_path(
    graph: dict[tuple[float, float], list[tuple[tuple[float, float], SegmentEdge]]],
    start: tuple[float, float],
    end: tuple[float, float],
) -> list[SegmentEdge]:
    if start not in graph or end not in graph:
        return []

    dist: dict[tuple[float, float], float] = {start: 0.0}
    prev: dict[tuple[float, float], tuple[tuple[float, float], SegmentEdge]] = {}
    heap: list[tuple[float, tuple[float, float]]] = [(0.0, start)]

    while heap:
        current_dist, node = heapq.heappop(heap)
        if node == end:
            break
        if current_dist > dist.get(node, float("inf")):
            continue

        for nxt, edge in graph.get(node, []):
            candidate = current_dist + edge.distance_km
            if candidate < dist.get(nxt, float("inf")):
                dist[nxt] = candidate
                prev[nxt] = (node, edge)
                heapq.heappush(heap, (candidate, nxt))

    if start != end and end not in prev:
        return []

    # If start and end snap to the same node, reserve the nearest adjacent segment.
    if start == end:
        choices = [edge for _, edge in graph.get(start, [])]
        if not choices:
            return []
        return [min(choices, key=lambda e: e.distance_km)]

    path: list[SegmentEdge] = []
    cursor = end
    while cursor != start:
        parent, edge = prev[cursor]
        path.append(edge)
        cursor = parent
    path.reverse()
    return path


async def resolve_route(
    db: AsyncSession,
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    departure_time: datetime,
) -> tuple[list[dict], int]:
    """
    Resolve a route over seeded road segments using shortest path (Dijkstra).
    Returns ordered segments and estimated total journey duration in minutes.
    """
    edges = await _load_edges(db)
    if not edges:
        raise RouteNotFoundError("Road network is empty; cannot resolve route")

    graph, node_positions = _build_graph(edges)
    start_node = _nearest_node(origin_lat, origin_lng, node_positions)
    end_node = _nearest_node(dest_lat, dest_lng, node_positions)

    path = _shortest_path(graph, start_node, end_node)
    if not path:
        raise RouteNotFoundError("No valid path found between origin and destination")

    start_point = node_positions[start_node]
    end_point = node_positions[end_node]
    approach_km = (
        _haversine_km(origin_lat, origin_lng, start_point[0], start_point[1])
        + _haversine_km(dest_lat, dest_lng, end_point[0], end_point[1])
    )
    approach_minutes = int(round((approach_km / AVERAGE_SPEED_KMPH) * 60)) if approach_km > 0 else 0

    segments: list[dict] = []
    trip_cursor = departure_time
    driving_minutes = 0

    for edge in path:
        segment_departure = trip_cursor
        slot_start = segment_departure.replace(minute=0, second=0, microsecond=0)
        slot_end = slot_start + timedelta(hours=1)
        duration_minutes = _to_minutes(edge.distance_km)

        segments.append(
            {
                "segment_id": edge.segment_id,
                "region": edge.region,
                "slot_start": slot_start,
                "slot_end": slot_end,
                "distance_km": edge.distance_km,
                "duration_minutes": duration_minutes,
                "start_lat": edge.start_lat,
                "start_lng": edge.start_lng,
                "end_lat": edge.end_lat,
                "end_lng": edge.end_lng,
            }
        )

        trip_cursor = trip_cursor + timedelta(minutes=duration_minutes)
        driving_minutes += duration_minutes

    total_minutes = max(1, driving_minutes + approach_minutes)
    return segments, total_minutes