"""Drill generation agents package."""

from app.agents.drill.coding_drill_agent import coding_drill_agent
from app.agents.drill.debugging_drill_agent import debugging_drill_agent
from app.agents.drill.design_drill_agent import design_drill_agent
from app.agents.drill.evaluator_agent import evaluator_agent

# Configurable number of generators to run in parallel (1-3)
HOW_MANY_GENERATORS = 3

__all__ = [
    "coding_drill_agent",
    "debugging_drill_agent",
    "design_drill_agent",
    "evaluator_agent",
    "HOW_MANY_GENERATORS",
]
