"""CLI demo for the charging copilot — chat without running the HTTP server.

Usage:
    python -m scripts.demo                      # runs a scripted demo reel
    python -m scripts.demo "your question"      # one-off question

Requires the LLM stack installed and ANTHROPIC_API_KEY set (see .env.example).
The scripted questions are chosen to show grounding: each forces a tool call.
"""

from __future__ import annotations

import sys

DEMO_QUESTIONS = [
    "I'm in Lyon with a Tesla Model 3 at 60%. Cheapest fast charger nearby with a café, and is it free right now?",
    "Can I drive Paris to Bordeaux in a Peugeot e-208 starting at 70%? Plan the stops and total cost.",
    "How does roaming work if I charge at a Fastned station with my Electra account?",
    "Is ELEC-PAR-02 available right now, and what does it cost?",
]


def main() -> None:
    """Run a one-off question if given, else the scripted demo reel."""
    from app.agent import ask  # imported here so --help works without the LLM stack

    questions = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else DEMO_QUESTIONS
    for q in questions:
        print(f"\n\033[1m🔌 {q}\033[0m")
        print(ask(q))


if __name__ == "__main__":
    main()
