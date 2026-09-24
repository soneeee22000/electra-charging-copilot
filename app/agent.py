"""The LangGraph agent: a grounded charging copilot.

A ReAct-style agent (LangGraph prebuilt) bound to the charging tools and a Claude
model. The system prompt enforces the core discipline: the model converses and
explains, but every factual claim about stations, availability, routing or pricing
MUST come from a tool call — no invented charger data. The design rationale:
RAG/tools provide ground truth, the LLM is the interface, not the source of facts.
"""

from __future__ import annotations

from functools import lru_cache

from .config import get_settings
from .tools import all_tools

SYSTEM_PROMPT = """You are the Electra Charging Copilot, a conversational assistant for EV drivers.

Rules you must follow:
1. NEVER invent stations, prices, availability, or routes. Every factual claim must come from a tool result.
2. To recommend a station, first find it (find_charging_stations) AND check it is available now (get_station_live_status).
3. For any trip or "can I reach" question, call plan_charging_route. Report its stops, minutes and cost as given.
4. For "how does X work" charging questions (roaming, autocharge, Plug & Charge, pricing, idle fees), call search_charging_knowledge.
5. If tools cannot answer, say so plainly rather than guessing.
6. Be concise and practical. Show costs in EUR and durations in minutes. Mention the connector when relevant.
"""


@lru_cache
def get_agent():  # type: ignore[no-untyped-def]
    """Build (once) and return the compiled LangGraph agent.

    Imports the LLM stack lazily so the rest of the package stays importable
    without langchain/langgraph installed or an API key set.
    """
    from langchain_anthropic import ChatAnthropic
    from langgraph.prebuilt import create_react_agent

    settings = get_settings()
    llm = ChatAnthropic(
        model=settings.model,
        temperature=settings.temperature,
        api_key=settings.anthropic_api_key or None,
    )
    return create_react_agent(llm, all_tools(), prompt=SYSTEM_PROMPT)


def ask(question: str) -> str:
    """Run one user turn through the agent and return the final text answer."""
    agent = get_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content
