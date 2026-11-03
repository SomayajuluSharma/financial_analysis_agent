
import json
import math

import yfinance as yf
from strands import tool

from financial_analysis_agent.tools.financial_tools import (
    get_cash_flow_statement,
    get_balance_sheet,
)


def _parse_result(result):
    if isinstance(result, dict):
        return result

    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Could not parse tool response"}

    return {"error": "Unexpected tool response"}


def _number(values, *names):
    for name in names:
        value = values.get(name)
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        ):
            return float(value)
    return None


@tool
def run_dcf_model(
    ticker: str,
    fcf_growth: float = 0.08,
    discount_rate: float = 0.10,
    terminal_growth: float = 0.025,
    forecast_years: int = 5,
) -> str:
    """
    Estimate enterprise value using a simplified discounted cash flow model.
    Growth and discount rates are assumptions, not predictions.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        return json.dumps({"error": "Ticker cannot be empty"})

    assumptions = [fcf_growth, discount_rate, terminal_growth]
    if not all(math.isfinite(x) for x in assumptions):
        return json.dumps({"error": "Assumptions must be finite numbers"})

    if not 1 <= forecast_years <= 10:
        return json.dumps({"error": "forecast_years must be between 1 and 10"})

    if fcf_growth <= -1:
        return json.dumps({"error": "fcf_growth must be greater than -1"})

    if terminal_growth < 0 or discount_rate <= terminal_growth:
        return json.dumps({
            "error": "discount_rate must be greater than terminal_growth, "
                     "and terminal_growth cannot be negative"
        })

    try:
        cash_flow = _parse_result(get_cash_flow_statement(ticker))
        balance_sheet = _parse_result(get_balance_sheet(ticker))

        if "error" in cash_flow:
            return json.dumps({
                "error": "Could not retrieve cash flow statement",
                "details": cash_flow["error"],
            })

        cash_values = cash_flow.get("data", {}).get("values", {})
        balance_values = balance_sheet.get("data", {}).get("values", {})

        operating_cf = _number(
            cash_values,
            "Operating Cash Flow",
            "Cash Flow From Continuing Operating Activities",
        )
        capex = _number(
            cash_values,
            "Capital Expenditure",
            "Capital Expenditures",
        )

        # Yahoo Finance commonly reports capital expenditure as negative.
        if operating_cf is None or capex is None:
            return json.dumps({
                "error": "Required operating cash flow or capital "
                         "expenditure data is unavailable"
            })

        historical_fcf = operating_cf + capex if capex < 0 else operating_cf - capex

        if historical_fcf <= 0:
            return json.dumps({
                "error": "This simplified DCF requires positive historical FCF"
            })

        projected_cash_flows = []
        present_value_cash_flows = 0.0

        for year in range(1, forecast_years + 1):
            projected_fcf = historical_fcf * (1 + fcf_growth) ** year
            present_value = projected_fcf / (1 + discount_rate) ** year

            projected_cash_flows.append({
                "year": year,
                "projected_fcf": projected_fcf,
                "present_value": present_value,
            })
            present_value_cash_flows += present_value

        terminal_fcf = (
            historical_fcf
            * (1 + fcf_growth) ** forecast_years
            * (1 + terminal_growth)
        )
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        present_value_terminal = (
            terminal_value / (1 + discount_rate) ** forecast_years
        )

        enterprise_value = present_value_cash_flows + present_value_terminal

        # Supplementary market data is fetched only for cash, debt and shares.
        info = yf.Ticker(ticker).get_info()
        cash = info.get("totalCash")
        debt = info.get("totalDebt")
        shares = info.get("sharesOutstanding")

        equity_value = None
        value_per_share = None

        if (
            isinstance(cash, (int, float))
            and isinstance(debt, (int, float))
        ):
            equity_value = enterprise_value + cash - debt

            if (
                isinstance(shares, (int, float))
                and shares > 0
            ):
                value_per_share = equity_value / shares

        return json.dumps({
            "ticker": ticker,
            "company_name": balance_sheet.get("company_name", ticker),
            "currency": balance_sheet.get("currency", "USD"),
            "source": balance_sheet.get("source", "Financial data tools"),
            "period": cash_flow.get("data", {}).get("period"),
            "method": "Simplified DCF",
            "historical_free_cash_flow": historical_fcf,
            "assumptions": {
                "fcf_growth": fcf_growth,
                "discount_rate": discount_rate,
                "terminal_growth": terminal_growth,
                "forecast_years": forecast_years,
            },
            "projected_cash_flows": projected_cash_flows,
            "present_value_of_forecast_cash_flows": present_value_cash_flows,
            "terminal_value": terminal_value,
            "present_value_of_terminal_value": present_value_terminal,
            "estimated_enterprise_value": enterprise_value,
            "estimated_equity_value": equity_value,
            "estimated_value_per_share": value_per_share,
            "limitations": [
                "This is a simplified model driven by explicit assumptions.",
                "Historical FCF growth may not predict future performance.",
                "Cash, debt, and share data may be unavailable or stale.",
                "This is not personalized investment advice.",
            ],
        }, indent=2, allow_nan=False)

    except Exception as exc:
        return json.dumps({
            "ticker": ticker,
            "error": "DCF calculation failed",
            "details": str(exc),
        })


@tool
def get_peer_multiples(ticker: str) -> str:
    """
    Retrieve available valuation multiples and sector metadata.
    This tool does not claim to calculate peer-group averages.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        return json.dumps({"error": "Ticker cannot be empty"})

    try:
        info = yf.Ticker(ticker).get_info()

        multiples = {
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "price_to_book": info.get("priceToBook"),
            "enterprise_value_to_ebitda": info.get("enterpriseToEbitda"),
        }

        return json.dumps({
            "ticker": ticker,
            "company_name": info.get("longName", ticker),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency"),
            "valuation_multiples": multiples,
            "note": (
                "These are the company's own multiples. Actual peer "
                "multiples and peer-group averages have not been calculated."
            ),
            "limitations": [
                "Unavailable provider fields are returned as null.",
                "Provider data may be delayed or incomplete.",
            ],
        }, indent=2, allow_nan=False)

    except Exception as exc:
        return json.dumps({
            "ticker": ticker,
            "error": "Peer multiples retrieval failed",
            "details": str(exc),
        })
