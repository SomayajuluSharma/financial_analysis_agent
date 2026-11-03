
from strands import Agent

from financial_analysis_agent.config.model import create_model
from financial_analysis_agent.tools.valuation_tools import (
    run_dcf_model,
    get_peer_multiples,
)


def create_valuation_agent():
    return Agent(
        model=create_model(),
        tools=[
            run_dcf_model,
            get_peer_multiples,
        ],
        system_prompt="""
You are the Valuation Agent.

1. Use run_dcf_model to estimate enterprise value.
2. Use get_peer_multiples to retrieve the company's available multiples.
3. Explain all DCF assumptions and limitations.
4. Distinguish enterprise value from equity value and value per share.
5. Never claim a peer-group comparison was performed unless peer data exists.
6. Never invent missing values.
7. Do not make unsupported buy or sell recommendations.
""",
    )
