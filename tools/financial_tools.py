
import json
import math

import yfinance as yf
from strands import tool

from financial_analysis_agent.tools.cache import get_or_fetch


def latest_column_summary(dataframe):
    """Convert the latest available statement to JSON-safe data."""

    if dataframe is None or dataframe.empty:
        return {}

    latest_period = dataframe.columns[0]
    values = {}

    for row_name, value in dataframe[latest_period].items():
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue

        if not math.isfinite(number):
            continue

        values[str(row_name)] = number

    return {
        "period": str(latest_period),
        "values": values,
    }


def _fetch_financial_bundle(ticker):
    """Fetch all financial statements, using the shared cache."""

    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker cannot be empty")

    cache_key = f"financials:{ticker}:annual"

    def fetch():
        company = yf.Ticker(ticker)
        info = company.get_info()

        return json.dumps(
            {
                "ticker": ticker,
                "company_name": info.get("longName"),
                "currency": info.get("currency"),
                "source": "Yahoo Finance via yfinance",
                "income_statement": latest_column_summary(
                    company.financials
                ),
                "balance_sheet": latest_column_summary(
                    company.balance_sheet
                ),
                "cash_flow_statement": latest_column_summary(
                    company.cashflow
                ),
            },
            allow_nan=False,
        )

    result = get_or_fetch(
        key=cache_key,
        fetch_function=fetch,
        ttl_seconds=300,
    )

    data = json.loads(result)

    if "error" in data:
        raise ValueError(data["error"])

    return data


def _get_statement(ticker, statement_name):
    """Return a selected financial statement."""

    try:
        data = _fetch_financial_bundle(ticker)

        return json.dumps(
            {
                "ticker": data["ticker"],
                "company_name": data["company_name"],
                "currency": data["currency"],
                "source": data["source"],
                "statement": statement_name,
                "data": data.get(statement_name, {}),
            },
            allow_nan=False,
        )

    except Exception as exc:
        return json.dumps(
            {
                "ticker": ticker.strip().upper(),
                "error": f"{type(exc).__name__}: {exc}",
            }
        )


@tool
def get_income_statement(ticker: str) -> str:
    """
    Get annual income statement data.

    Includes revenue, net income, operating income, gross profit,
    and EPS when available.
    """
    return _get_statement(ticker, "income_statement")


@tool
def get_balance_sheet(ticker: str) -> str:
    """
    Get annual balance sheet data.

    Includes assets, liabilities, cash, and debt when available.
    """
    return _get_statement(ticker, "balance_sheet")


@tool
def get_cash_flow_statement(ticker: str) -> str:
    """
    Get annual cash flow statement data.

    Includes operating cash flow, capital expenditure,
    and free cash flow when available.
    """
    return _get_statement(ticker, "cash_flow_statement")


def _find_metric(statement, *possible_names):
    """Find a financial metric without relying on exact capitalization."""

    values = statement.get("values", {})

    normalized = {
        key.lower().replace("_", " ").strip(): value
        for key, value in values.items()
    }

    for name in possible_names:
        key = name.lower().replace("_", " ").strip()

        if key in normalized:
            return normalized[key]

    return None


def _safe_ratio(numerator, denominator):
    """Calculate a ratio only when both values are available."""

    if numerator is None or denominator is None or denominator == 0:
        return None

    return numerator / denominator


@tool
def compute_key_ratios(ticker: str) -> str:
    """
    Calculate key financial ratios from cached financial statements.

    Returns margins, liquidity, leverage, ROA, and ROE where
    the required source figures are available.
    """

    try:
        data = _fetch_financial_bundle(ticker)

        income = data.get("income_statement", {})
        balance = data.get("balance_sheet", {})
        cash_flow = data.get("cash_flow_statement", {})

        revenue = _find_metric(
            income, "Total Revenue", "Operating Revenue"
        )
        net_income = _find_metric(income, "Net Income")
        operating_income = _find_metric(
            income, "Operating Income", "EBIT"
        )
        gross_profit = _find_metric(income, "Gross Profit")

        current_assets = _find_metric(balance, "Current Assets")
        current_liabilities = _find_metric(
            balance, "Current Liabilities"
        )
        total_assets = _find_metric(balance, "Total Assets")
        total_debt = _find_metric(balance, "Total Debt")
        stockholders_equity = _find_metric(
            balance,
            "Stockholders Equity",
            "Total Stockholder Equity",
            "Total Equity Gross Minority Interest",
        )

        operating_cash_flow = _find_metric(
            cash_flow, "Operating Cash Flow",
            "Total Cash From Operating Activities"
        )
        free_cash_flow = _find_metric(cash_flow, "Free Cash Flow")

        ratios = {
            "net_profit_margin": _safe_ratio(net_income, revenue),
            "operating_margin": _safe_ratio(operating_income, revenue),
            "gross_margin": _safe_ratio(gross_profit, revenue),
            "current_ratio": _safe_ratio(
                current_assets, current_liabilities
            ),
            "debt_to_equity": _safe_ratio(
                total_debt, stockholders_equity
            ),
            "return_on_assets": _safe_ratio(
                net_income, total_assets
            ),
            "return_on_equity": _safe_ratio(
                net_income, stockholders_equity
            ),
            "operating_cash_flow_to_revenue": _safe_ratio(
                operating_cash_flow, revenue
            ),
            "free_cash_flow_margin": _safe_ratio(
                free_cash_flow, revenue
            ),
        }

        # Keep raw ratios as decimals; for example, 0.25 means 25%.
        return json.dumps(
            {
                "ticker": data["ticker"],
                "company_name": data["company_name"],
                "currency": data["currency"],
                "source": data["source"],
                "income_statement_period": income.get("period"),
                "balance_sheet_period": balance.get("period"),
                "cash_flow_period": cash_flow.get("period"),
                "ratios": ratios,
                "note": (
                    "Ratios are decimals, not percentages. "
                    "Null means the required data was unavailable "
                    "or the denominator was zero. ROA and ROE use "
                    "reported period-end balances, not average balances."
                ),
            },
            allow_nan=False,
        )

    except Exception as exc:
        return json.dumps(
            {
                "ticker": ticker.strip().upper(),
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
