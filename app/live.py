"""Deterministic mock of a live OCPI status feed.

A real deployment would read an operator's real-time supervision data (for
example OCPP heartbeats and EVSE status aggregated by a message bus). Here it is
a pure function of station_id so the demo and tests are reproducible without a backend.
"""

from __future__ import annotations

from typing import List

from .data import stations_by_id
from .models import LiveStatus


def _seed(station_id: str) -> int:
    """Stable integer derived from the id (no global RNG, fully deterministic)."""
    return sum(ord(c) for c in station_id)


def live_status(station_id: str) -> LiveStatus:
    """Return a deterministic live availability roll-up for one station."""
    catalog = stations_by_id()
    station = catalog.get(station_id)
    total = station.num_points if station else 0
    seed = _seed(station_id)
    is_operational = seed % 11 != 0  # ~9% of sites flagged down for realism
    available = 0 if not is_operational else seed % (total + 1)
    return LiveStatus(
        station_id=station_id,
        available_points=available,
        total_points=total,
        is_operational=is_operational,
    )


def available_now(station_ids: List[str]) -> List[LiveStatus]:
    """Live status for a batch of stations, available ones first."""
    statuses = [live_status(sid) for sid in station_ids]
    return sorted(statuses, key=lambda s: (not s.is_available, -s.available_points))
