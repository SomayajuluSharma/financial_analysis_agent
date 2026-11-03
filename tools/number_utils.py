
import math


def normalize_number(value):
    """
    Return a finite int or float.
    Reject booleans, missing values, NaN, and infinity.
    """

    if value is None or isinstance(value, bool):
        return None

    if not isinstance(value, (int, float)):
        return None

    if not math.isfinite(value):
        return None

    # Preserve integers rather than converting them to floats.
    if isinstance(value, int):
        return value

    # Avoid unnecessary .0 for whole-number floats.
    if value.is_integer():
        return int(value)

    return value


def format_financial_value(value, currency="USD"):
    """Format a raw financial amount for human-readable output."""

    number = normalize_number(value)

    if number is None:
        return "Unavailable"

    sign = "-" if number < 0 else ""
    amount = abs(number)

    if amount >= 1_000_000_000:
        formatted = f"{amount / 1_000_000_000:,.2f} billion"
    elif amount >= 1_000_000:
        formatted = f"{amount / 1_000_000:,.2f} million"
    elif amount >= 1_000:
        formatted = f"{amount:,.2f}"
    else:
        formatted = f"{amount:g}"

    currency_symbols = {
        "USD": "$",
        "INR": "₹",
        "EUR": "€",
        "GBP": "£",
    }

    symbol = currency_symbols.get(currency.upper(), f"{currency} ")

    return f"{sign}{symbol}{formatted}"
