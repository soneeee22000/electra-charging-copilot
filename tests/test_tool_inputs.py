"""Tool wrappers must not silently widen or relabel what the model asked for."""

from __future__ import annotations

import pytest

pytest.importorskip("langchain_core")
pytest.importorskip("chromadb")

from app.tools import find_charging_stations, plan_charging_route  # noqa: E402

CCS_ONLY_STATION = "ELEC-PAR-02"


def test_connector_filter_is_case_insensitive() -> None:
    """'type2' filters like 'Type2' instead of being dropped."""
    out = find_charging_stations.invoke({"connector": "type2"})
    assert "ELEC-PAR-01" in out
    assert CCS_ONLY_STATION not in out


def test_unknown_connector_is_reported_not_ignored() -> None:
    """An unknown connector returns a message, not the unfiltered catalog."""
    out = find_charging_stations.invoke({"connector": "Tesla-NACS"})
    assert CCS_ONLY_STATION not in out
    assert "unknown connector" in out.lower()


def test_route_tool_discloses_default_car_profile() -> None:
    """The route tool says when it fell back to the default car profile."""
    out = plan_charging_route.invoke(
        {"origin": "Paris", "destination": "Lyon", "current_battery_pct": 80, "car_model": "Tesla Model Y"}
    )
    assert "default" in out.lower()
    assert "Tesla Model Y" in out
