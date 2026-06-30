"""RAG knowledge base over Chroma.

Builds an in-memory vector store from (a) one document per station and (b) a
small set of charging policy/FAQ documents, then exposes a retriever. Chroma's
default embedding function (a lightweight ONNX MiniLM) is used so the demo runs
without a separate embeddings API key.

chromadb is imported lazily so the routing/data core stays importable without
the vector stack installed.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from .config import get_settings
from .data import STATIONS

# Charging policy / FAQ corpus the assistant can ground answers in. In
# production these would be real help-centre and ops documents.
POLICY_DOCS: List[tuple[str, str]] = [
    ("roaming", "Electra is part of the Spark Alliance roaming network with Fastned, Ionity and Atlante. "
                "Drivers can charge across partner stations on one Electra account via OCPI; partner sessions "
                "may be billed at the partner's tariff, which is usually higher than Electra's own."),
    ("autocharge", "Autocharge lets a registered vehicle start charging automatically when the cable is plugged "
                   "in, with no app or badge, by recognising the car. Plug & Charge (ISO 15118) is the secure, "
                   "certificate-based successor and is rolling out across the network."),
    ("pricing", "Electra bills per kWh consumed, not per minute. Typical Electra tariffs are around 0.37-0.43 EUR/kWh. "
                "An Electra+ Boost subscription gives preferential rates across Electra and Spark Alliance partners."),
    ("idle_fee", "To keep fast chargers free for others, an idle/overstay fee may apply if a vehicle remains "
                 "connected after charging completes. Move the car promptly once charging ends."),
    ("connectors", "Ultra-fast DC charging uses the CCS connector. Type2 is for slower AC charging. Most EVs sold "
                   "in Europe use CCS for DC fast charging; check your car's port before planning a fast-charge stop."),
    ("charging_curve", "DC charging is fastest between roughly 10% and 80% state of charge, then slows sharply. "
                       "For road trips, charging to 80% and driving on is usually faster than waiting for 100%."),
]


def _station_doc(station_id: str) -> str:
    """Render a station as a retrievable natural-language document."""
    s = next(st for st in STATIONS if st.station_id == station_id)
    connectors = ", ".join(c.value for c in s.connectors)
    amenities = ", ".join(s.amenities) if s.amenities else "no listed amenities"
    return (
        f"{s.name} ({s.station_id}) is a {s.operator} charging station in {s.city}. "
        f"Up to {s.max_power_kw} kW, {s.num_points} charge points, connectors: {connectors}. "
        f"Tariff about {s.tariff_eur_per_kwh:.2f} EUR/kWh. Amenities: {amenities}."
    )


@lru_cache
def _collection():  # type: ignore[no-untyped-def]
    """Build (once) and return the Chroma collection with all KB documents."""
    import chromadb  # lazy import

    client = chromadb.EphemeralClient()
    coll = client.get_or_create_collection(get_settings().chroma_collection)
    docs, ids, metas = [], [], []
    for station in STATIONS:
        docs.append(_station_doc(station.station_id))
        ids.append(f"station::{station.station_id}")
        metas.append({"kind": "station", "ref": station.station_id})
    for key, text in POLICY_DOCS:
        docs.append(text)
        ids.append(f"policy::{key}")
        metas.append({"kind": "policy", "ref": key})
    coll.add(documents=docs, ids=ids, metadatas=metas)
    return coll


def retrieve(query: str, k: int | None = None) -> List[str]:
    """Return the top-k knowledge-base passages most relevant to `query`."""
    top_k = k or get_settings().max_retrieved_docs
    result = _collection().query(query_texts=[query], n_results=top_k)
    documents = result.get("documents") or [[]]
    return documents[0]
