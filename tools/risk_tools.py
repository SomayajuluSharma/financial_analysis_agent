
import json

from strands import tool

from financial_analysis_agent.tools.financial_tools import (
    get_balance_sheet,
    compute_key_ratios,
)
from financial_analysis_agent.tools.news_tools import search_recent_news


def _parse_tool_result(result):
    """Convert a JSON tool response into a Python dictionary."""
    if isinstance(result, dict):
        return result

    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Could not parse tool response"}

    return {"error": "Unexpected tool response type"}


def _get_metric(values, *possible_names):
    """Find a metric using alternative provider field names."""
    for name in possible_names:
        value = values.get(name)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
    return None


@tool
def assess_financial_risks(ticker: str) -> str:
    """
    Assess liquidity, leverage, profitability, cash flow and news risks
    for a publicly traded company using available financial data.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        return json.dumps({"error": "Ticker cannot be empty"})

    try:
        balance = _parse_tool_result(get_balance_sheet(ticker))
        ratios = _parse_tool_result(compute_key_ratios(ticker))
        news = _parse_tool_result(search_recent_news(ticker))

        if "error" in balance:
            return json.dumps({
                "ticker": ticker,
                "error": "Balance sheet retrieval failed",
                "details": balance["error"],
            })

        balance_values = balance.get("data", {}).get("values", {})
        ratio_values = ratios.get("ratios", {})
        news_items = news.get("articles", [])

        current_assets = _get_metric(
            balance_values, "Current Assets", "Total Current Assets"
        )
        current_liabilities = _get_metric(
            balance_values, "Current Liabilities", "Total Current Liabilities"
        )
        total_debt = _get_metric(
            balance_values, "Total Debt", "Long Term Debt"
        )
        equity = _get_metric(
            balance_values, "Stockholders Equity",
            "Common Stock Equity", "Total Equity Gross Minority Interest"
        )

        flags = []

        current_ratio = ratio_values.get("current_ratio")
        debt_to_equity = ratio_values.get("debt_to_equity")
        net_profit_margin = ratio_values.get("net_profit_margin")
        operating_cash_flow_to_revenue = ratio_values.get(
            "operating_cash_flow_to_revenue"
        )
        free_cash_flow_margin = ratio_values.get("free_cash_flow_margin")

        if current_ratio is not None:
            if current_ratio < 1:
                flags.append({
                    "risk": "Liquidity risk",
                    "severity": "High",
                    "evidence": (
                        f"Current ratio is {current_ratio:.2f}; "
                        "current liabilities exceed current assets."
                    ),
                })
            elif current_ratio < 1.5:
                flags.append({
                    "risk": "Liquidity risk",
                    "severity": "Moderate",
                    "evidence": f"Current ratio is {current_ratio:.2f}.",
                })

        if debt_to_equity is not None and debt_to_equity > 2:
            flags.append({
                "risk": "Leverage risk",
                "severity": "High",
                "evidence": f"Debt-to-equity ratio is {debt_to_equity:.2f}.",
            })
        elif debt_to_equity is not None and debt_to_equity > 1:
            flags.append({
                "risk": "Leverage risk",
                "severity": "Moderate",
                "evidence": f"Debt-to-equity ratio is {debt_to_equity:.2f}.",
            })

        if net_profit_margin is not None and net_profit_margin < 0:
            flags.append({
                "risk": "Profitability risk",
                "severity": "High",
                "evidence": (
                    f"Net profit margin is {net_profit_margin:.2%}."
                ),
            })

        if (
            operating_cash_flow_to_revenue is not None
            and operating_cash_flow_to_revenue < 0
        ):
            flags.append({
                "risk": "Operating cash flow risk",
                "severity": "High",
                "evidence": (
                    "Operating cash flow relative to revenue is negative."
                ),
            })

        if free_cash_flow_margin is not None and free_cash_flow_margin < 0:
            flags.append({
                "risk": "Free cash flow risk",
                "severity": "High",
                "evidence": "Free cash flow margin is negative.",
            })

        if not flags:
            flags.append({
                "risk": "No threshold-based financial risk detected",
                "severity": "Unclassified",
                "evidence": (
                    "Available metrics did not cross the configured "
                    "risk thresholds. This does not mean the company "
                    "is risk-free."
                ),
            })

        return json.dumps({
            "ticker": ticker,
            "company_name": balance.get("company_name", ticker),
            "currency": balance.get("currency", "USD"),
            "source": balance.get("source", "Financial data tools"),
            "period": balance.get("data", {}).get("period"),
            "metrics": {
                "current_assets": current_assets,
                "current_liabilities": current_liabilities,
                "total_debt": total_debt,
                "equity": equity,
                "current_ratio": current_ratio,
                "debt_to_equity": debt_to_equity,
                "net_profit_margin": net_profit_margin,
                "operating_cash_flow_to_revenue":
                    operating_cash_flow_to_revenue,
                "free_cash_flow_margin": free_cash_flow_margin,
            },
            "risk_flags": flags,
            "recent_news": news_items,
            "limitations": [
                "Risk thresholds are simple heuristics, not universal rules.",
                "News availability and sentiment may be incomplete.",
                "This output is not personalized investment advice.",
            ],
        }, indent=2, allow_nan=False)

    except Exception as exc:
        return json.dumps({
            "ticker": ticker,
            "error": "Risk assessment failed",
            "details": str(exc),
        })
