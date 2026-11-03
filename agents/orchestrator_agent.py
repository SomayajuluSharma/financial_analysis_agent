import logging
from concurrent.futures import ThreadPoolExecutor

from strands import Agent

from financial_analysis_agent.config.model import create_model
from financial_analysis_agent.agents.financial_data_agent import (
    create_financial_data_agent,
)
from financial_analysis_agent.agents.news_sentiment_agent import (
    create_news_sentiment_agent,
)
from financial_analysis_agent.agents.risk_agent import create_risk_agent
from financial_analysis_agent.agents.valuation_agent import (
    create_valuation_agent,
)
from financial_analysis_agent.agents.report_writer_agent import (
    create_report_writer_agent,
)

logger = logging.getLogger(__name__)


def _run_agent(name, agent, prompt):
    """Run an agent and return its result without hiding failures."""
    try:
        result = str(agent(prompt))
        return result
    except Exception as exc:
        logger.exception("%s failed", name)
        return f"AGENT FAILED: {name}. Error: {type(exc).__name__}: {exc}"


def create_orchestrator_agent():
    """
    Create the OrchestratorAgent with specialist agents exposed as tools.

    This provides the tool-based architecture shown in the bootcamp.
    For predictable phase ordering and parallel execution, use run_analysis().
    """
    financial_agent = create_financial_data_agent()
    news_agent = create_news_sentiment_agent()
    risk_agent = create_risk_agent()
    valuation_agent = create_valuation_agent()
    report_agent = create_report_writer_agent()

    specialist_tools = [
        financial_agent.as_tool(
            name="financial_data_agent",
            description=(
                "Retrieve income statement, balance sheet, cash flow, "
                "and key ratios for a stock ticker."
            ),
        ),
        news_agent.as_tool(
            name="news_sentiment_agent",
            description=(
                "Retrieve recent news and summarize evidence-based sentiment."
            ),
        ),
        risk_agent.as_tool(
            name="risk_agent",
            description=(
                "Assess liquidity, leverage, profitability, and business risks."
            ),
        ),
        valuation_agent.as_tool(
            name="valuation_agent",
            description=(
                "Estimate valuation using available DCF and valuation tools."
            ),
        ),
        report_agent.as_tool(
            name="report_writer_agent",
            description=(
                "Synthesize specialist findings into a concise final report."
            ),
        ),
    ]

    return Agent(
        name="OrchestratorAgent",
        model=create_model(),
        tools=specialist_tools,
        system_prompt="""
You are the director of a fundamental stock analysis.

Use the specialist tools to complete the analysis:
1. Obtain financial data, recent news, and risk analysis.
2. Use financial evidence as context for valuation.
3. Give all results to the report writer.
4. Return the report writer's result.

Do not invent financial figures, sources, dates, or tool results.
Clearly distinguish reported data from estimates and assumptions.
Disclose missing information and specialist failures.
Do not provide personalized financial advice.
"""
    )


def run_analysis(ticker):
    """
    Run the research phases deterministically:
    1. Financial data, news, and risk concurrently.
    2. Valuation after financial data is available.
    3. Report writing after all specialist results are available.
    """
    ticker = ticker.strip().upper()

    if not ticker or not ticker.replace(".", "").replace("-", "").isalnum():
        raise ValueError("Invalid ticker symbol.")

    financial_agent = create_financial_data_agent()
    news_agent = create_news_sentiment_agent()
    risk_agent = create_risk_agent()
    valuation_agent = create_valuation_agent()
    report_agent = create_report_writer_agent()

    prompts = {
        "financial": (
            f"Analyze {ticker}. Retrieve income statement, balance sheet, "
            "cash flow statement, and key ratios. Report values, units, "
            "reporting periods, and missing data. Keep the result concise."
        ),
        "news": (
            f"Find recent news relevant to {ticker}. Summarize up to 5 "
            "relevant headlines with publisher, date, URL when available, "
            "and evidence-based sentiment. Do not invent missing details."
        ),
        "risk": (
            f"Assess financial and business risks for {ticker}. Use available "
            "balance-sheet, ratio, and news tools. Return the most important "
            "risks with evidence, potential impact, and missing information. "
            "Keep the result under 350 words."
        ),
    }

    # Phase 1: independent research tasks run concurrently.
    agents = {
        "financial": financial_agent,
        "news": news_agent,
        "risk": risk_agent,
    }

    print("\n[Phase 1/3] Running financial, news, and risk research in parallel...")

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            name: executor.submit(
                _run_agent, name, agent, prompts[name]
            )
            for name, agent in agents.items()
        }
        results = {
            name: future.result()
            for name, future in futures.items()
        }

    # Phase 2: valuation gets the financial context.
    print("\n[Phase 2/3] Running valuation...")

    valuation_prompt = f"""
Analyze the valuation of {ticker} using available valuation tools.

Financial evidence:
{results['financial']}

Explain the DCF assumptions, including growth, discount rate,
terminal growth, and forecast period when available.
Distinguish reported figures from estimates.
Do not claim peer comparison without actual peer data.
If data is missing or a tool fails, disclose that limitation.
Keep the result concise.
"""

    results["valuation"] = _run_agent(
        "valuation",
        valuation_agent,
        valuation_prompt,
    )

    # Phase 3: synthesize all results.
    print("\n[Phase 3/3] Writing final report...")

    report_prompt = f"""
Write a concise fundamental analysis report for {ticker} using ONLY
the specialist results below.

Include:
1. Executive summary
2. Financial performance and key ratios
3. News and sentiment
4. Main financial risks
5. Valuation assumptions and limitations
6. Missing data
7. Evidence-based conclusion

Do not invent figures, news, dates, sources, or comparisons.
Clearly distinguish reported facts from estimates.
Disclose any failed agent or missing evidence.
Do not provide personalized financial advice.

FINANCIAL DATA:
{results['financial']}

NEWS AND SENTIMENT:
{results['news']}

RISK ASSESSMENT:
{results['risk']}

VALUATION:
{results['valuation']}
"""

    results["report"] = _run_agent(
        "report_writer",
        report_agent,
        report_prompt,
    )

    return results
