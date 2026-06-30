"""Tests for the LangChain tools and the RAG retriever.

These exercise the tool wrappers and the Chroma vector store directly — no LLM
call, so they need no API key (the first RAG run downloads a small embedding
model). Skipped automatically if the optional stack is not installed.
"""

from __future__ import annotations

import pytest

pytest.importorskip("langchain_core")
pytest.importorskip("chromadb")

from app.tools import (  # noqa: E402
    find_charging_stations,
    get_station_live_status,
    plan_charging_route,
    search_charging_knowledge,
)


def test_find_tool_returns_lyon_station() -> None:
    """The find tool surfaces the Lyon station with its id."""
    out = find_charging_stations.invoke({"city": "Lyon"})
    assert "ELEC-LYO-01" in out


def test_live_status_tool() -> None:
    """The live-status tool reports operational state for a known station."""
    out = get_station_live_status.invoke({"station_id": "ELEC-PAR-01"})
    assert "ELEC-PAR-01" in out
    assert "operational" in out or "OUT OF SERVICE" in out


def test_route_tool_paris_dijon() -> None:
    """The route tool returns a plan string for a feasible trip."""
    out = plan_charging_route.invoke(
        {"origin": "Paris", "destination": "Dijon", "current_battery_pct": 90, "car_model": "Tesla Model 3"}
    )
    assert "Paris to Dijon" in out


@pytest.mark.slow
def test_rag_retrieves_roaming_passage() -> None:
    """The knowledge tool retrieves the roaming policy passage for a roaming query."""
    out = search_charging_knowledge.invoke({"query": "how does roaming work across partner networks"})
    assert "Spark Alliance" in out or "OCPI" in out or "roaming" in out.lower()
