"""Tests for the FastAPI structured endpoints (no LLM, no API key needed)."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_healthz() -> None:
    """Liveness returns ok."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_stations() -> None:
    """Catalog endpoint returns the seeded stations."""
    resp = client.get("/stations")
    assert resp.status_code == 200
    assert len(resp.json()) >= 12


def test_station_status_known_and_unknown() -> None:
    """Known id returns status; unknown id returns 404."""
    ok = client.get("/stations/ELEC-PAR-01/status")
    assert ok.status_code == 200
    assert "is_available" in ok.json()
    assert client.get("/stations/NOPE/status").status_code == 404


def test_route_feasible_and_infeasible() -> None:
    """Route endpoint reports feasibility for known and unknown cities."""
    ok = client.post("/route", json={"origin": "Paris", "destination": "Dijon", "current_battery_pct": 90})
    assert ok.status_code == 200 and ok.json()["feasible"] is True
    bad = client.post("/route", json={"origin": "Atlantis", "destination": "Paris"})
    assert bad.json()["feasible"] is False
