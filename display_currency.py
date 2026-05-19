"""Currency metadata and formatting for the Streamlit UI."""

from __future__ import annotations

from typing import TypedDict


class CurrencyInfo(TypedDict):
    symbol: str
    name: str
    decimals: int


CURRENCIES: dict[str, CurrencyInfo] = {
    "USD": {"symbol": "$", "name": "US Dollar", "decimals": 0},
    "EUR": {"symbol": "€", "name": "Euro", "decimals": 0},
    "GBP": {"symbol": "£", "name": "British Pound", "decimals": 0},
    "JPY": {"symbol": "¥", "name": "Japanese Yen", "decimals": 0},
    "CHF": {"symbol": "CHF\u00a0", "name": "Swiss Franc", "decimals": 0},
    "CAD": {"symbol": "C$", "name": "Canadian Dollar", "decimals": 0},
    "AUD": {"symbol": "A$", "name": "Australian Dollar", "decimals": 0},
    "INR": {"symbol": "₹", "name": "Indian Rupee", "decimals": 0},
    "CNY": {"symbol": "¥", "name": "Chinese Yuan", "decimals": 0},
    "SGD": {"symbol": "S$", "name": "Singapore Dollar", "decimals": 0},
    "HKD": {"symbol": "HK$", "name": "Hong Kong Dollar", "decimals": 0},
    "SEK": {"symbol": "kr", "name": "Swedish Krona", "decimals": 0},
    "NOK": {"symbol": "kr", "name": "Norwegian Krone", "decimals": 0},
    "MXN": {"symbol": "MX$", "name": "Mexican Peso", "decimals": 0},
    "BRL": {"symbol": "R$", "name": "Brazilian Real", "decimals": 0},
    "ZAR": {"symbol": "R", "name": "South African Rand", "decimals": 0},
}


def format_money(amount: float, currency_code: str, *, compact: bool = False) -> str:
    """Format a monetary amount with the currency symbol."""
    info = CURRENCIES.get(currency_code, CURRENCIES["USD"])
    decimals = info["decimals"]
    sym = info["symbol"]
    if compact and abs(amount) >= 1_000_000:
        scaled = amount / 1_000_000
        body = f"{scaled:,.2f}M"
    elif compact and abs(amount) >= 1_000:
        scaled = amount / 1_000
        body = f"{scaled:,.2f}K"
    else:
        body = f"{amount:,.{decimals}f}"
    # Symbol-after for some currencies; keep prefix for consistency with Excel-style UI
    if sym.endswith("\u00a0"):
        return f"{sym}{body}"
    return f"{sym}{body}"


def currency_label(code: str) -> str:
    info = CURRENCIES[code]
    return f"{code} — {info['name']}"
