
from strands import Agent

from financial_analysis_agent.config.model import create_model
from financial_analysis_agent.tools.financial_tools import (
    get_income_statement,
    get_balance_sheet,
    get_cash_flow_statement,
    compute_key_ratios,
)


def create_financial_data_agent():
    return Agent(
        model=create_model(),
        tools=[
            get_income_statement,
            get_balance_sheet,
            get_cash_flow_statement,
            compute_key_ratios,
        ],
        system_prompt="""
You are the Financial Data Agent in a stock analysis system.

Responsibilities:
1. Retrieve income statement data when requested.
2. Retrieve balance sheet data when requested.
3. Retrieve cash flow statement data when requested.
4. Retrieve computed key ratios when requested.
5. Use tool results as the source of financial figures.
6. Never invent missing figures or ratios.
7. Include reporting periods, currency, and data source.
8. Explain ratios clearly and distinguish percentages from multiples.
9. Report unavailable metrics as unavailable.

Do not write the final investment report.
""",
    )
