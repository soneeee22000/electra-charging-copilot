"""Geographic helpers for the routing engine.

Pure functions, no external dependencies, fully unit-testable.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two lat/lon points."""
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def progress_along_route(
    origin: tuple[float, float],
    dest: tuple[float, float],
    point: tuple[float, float],
) -> float:
    """Fraction (0..1) of the origin→dest distance covered at the closest
    approach to `point`, via scalar projection. Used to order candidate
    charging stops by how far down the route they sit.
    """
    ox, oy = origin
    dx, dy = dest
    px, py = point
    route_vec = (dx - ox, dy - oy)
    point_vec = (px - ox, py - oy)
    denom = route_vec[0] ** 2 + route_vec[1] ** 2
    if denom == 0:
        return 0.0
    t = (point_vec[0] * route_vec[0] + point_vec[1] * route_vec[1]) / denom
    return max(0.0, min(1.0, t))


def detour_km(
    origin: tuple[float, float],
    dest: tuple[float, float],
    point: tuple[float, float],
) -> float:
    """Extra distance added by routing via `point` instead of going direct.

    Approximated as (origin→point) + (point→dest) − (origin→dest); a small,
    explainable proxy for true road detour cost.
    """
    direct = haversine_km(*origin, *dest)
    via = haversine_km(*origin, *point) + haversine_km(*point, *dest)
    return max(0.0, via - direct)
