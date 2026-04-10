"""Currency conversion tool using the Frankfurter API (no key required).

Uses ECB exchange rates via api.frankfurter.app.  Rates are cached per
conversion pair for the session to avoid repeated HTTP lookups.
Covers 30 major currencies (AUD, BRL, CAD, CHF, CNY, CZK, DKK, EUR,
GBP, HKD, HUF, IDR, ILS, INR, ISK, JPY, KRW, MXN, MYR, NOK, NZD,
PHP, PLN, RON, SEK, SGD, THB, TRY, USD, ZAR).
"""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request

from src.tools.registry import REGISTRY, ToolDefinition

_API_BASE = "https://api.frankfurter.app/latest"
_HEADERS = {"User-Agent": "jm-cl-assistant/1.0"}

# Supported currency codes (used for validation and UI display)
SUPPORTED_CODES = frozenset(
    {
        "AUD",
        "BRL",
        "CAD",
        "CHF",
        "CNY",
        "CZK",
        "DKK",
        "EUR",
        "GBP",
        "HKD",
        "HUF",
        "IDR",
        "ILS",
        "INR",
        "ISK",
        "JPY",
        "KRW",
        "MXN",
        "MYR",
        "NOK",
        "NZD",
        "PHP",
        "PLN",
        "RON",
        "SEK",
        "SGD",
        "THB",
        "TRY",
        "USD",
        "ZAR",
    }
)

# Common currency name / alias → ISO code
_NAME_TO_CODE: dict[str, str] = {
    "dollar": "USD",
    "dollars": "USD",
    "euro": "EUR",
    "euros": "EUR",
    "pound": "GBP",
    "pounds": "GBP",
    "sterling": "GBP",
    "yen": "JPY",
    "yuan": "CNY",
    "renminbi": "CNY",
    "rupee": "INR",
    "rupees": "INR",
    "won": "KRW",
    "ruble": "RUB",
    "rouble": "RUB",
    "franc": "CHF",
    "francs": "CHF",
    "krona": "SEK",
    "kronor": "SEK",  # Swedish
    "krone": "NOK",
    "kroner": "NOK",  # Norwegian/Danish (also DKK)
    "real": "BRL",
    "reais": "BRL",
    "peso": "MXN",
    "pesos": "MXN",
    "ringgit": "MYR",
    "baht": "THB",
    "lira": "TRY",
    "shekel": "ILS",
    "shekels": "ILS",
    "rand": "ZAR",
    "rupiah": "IDR",
    "zloty": "PLN",
    "zlotys": "PLN",
    "koruna": "CZK",
    "forint": "HUF",
    "leu": "RON",
    "lei": "RON",
    "dollar australian": "AUD",
    "australian dollar": "AUD",
    "canadian dollar": "CAD",
    "hong kong dollar": "HKD",
    "new zealand dollar": "NZD",
    "singapore dollar": "SGD",
    "philippine peso": "PHP",
    "south african rand": "ZAR",
    "south korean won": "KRW",
}

# Session-level rate cache: (from_code, to_code) → (rate, date_str)
_rate_cache: dict[tuple[str, str], tuple[float, str]] = {}

# Pattern: optional preamble, then <amount> <from> to/in <to>
_QUERY_RE = re.compile(
    r"(?:convert\s+|how\s+much\s+(?:is\s+)?)??"
    r"(\d[\d,]*(?:\.\d+)?)\s+"
    r"([a-zA-Z][a-zA-Z\s]{0,25}?)\s+"
    r"(?:to|in)\s+"
    r"([a-zA-Z][a-zA-Z\s]{0,25}?)"
    r"\s*[?.]?\s*$",
    re.IGNORECASE,
)


def _resolve_code(token: str) -> str | None:
    """Resolve a currency name or code to an uppercase ISO code.

    Args:
        token: A currency code (e.g. ``"USD"``) or name
          (e.g. ``"dollars"``).

    Returns:
        An uppercase ISO 4217 code, or ``None`` if unrecognised.
    """
    token = token.strip()
    upper = token.upper()
    if upper in SUPPORTED_CODES:
        return upper
    lower = token.lower()
    return _NAME_TO_CODE.get(lower)


def _fetch_rate(from_code: str, to_code: str) -> tuple[float, str] | None:
    """Fetch the exchange rate from Frankfurter and cache it.

    Args:
        from_code: ISO source currency code.
        to_code: ISO target currency code.

    Returns:
        ``(rate, date_str)`` or ``None`` on failure.
    """
    key = (from_code, to_code)
    if key in _rate_cache:
        return _rate_cache[key]

    params = urllib.parse.urlencode({"from": from_code, "to": to_code})
    url = f"{_API_BASE}?{params}"
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        logging.warning("Frankfurter API request failed: %s", exc)
        return None

    rate = data.get("rates", {}).get(to_code)
    date_str = data.get("date", "")
    if rate is None:
        return None

    _rate_cache[key] = (float(rate), date_str)
    return _rate_cache[key]


def convert_currency(amount: float, from_code: str, to_code: str) -> str:
    """Convert an amount between two currencies.

    Args:
        amount: The numeric quantity to convert.
        from_code: ISO source currency code, e.g. ``"USD"``.
        to_code: ISO target currency code, e.g. ``"EUR"``.

    Returns:
        A formatted result string such as
        ``"100.00 USD = 91.47 EUR (rate: 0.9147, ECB 2026-04-05)"``
        or an error message.
    """
    from_code = from_code.upper()
    to_code = to_code.upper()

    if from_code not in SUPPORTED_CODES:
        return f"Unsupported currency: {from_code}"
    if to_code not in SUPPORTED_CODES:
        return f"Unsupported currency: {to_code}"
    if from_code == to_code:
        return f"{amount:.2f} {from_code} = {amount:.2f} {to_code}"

    result = _fetch_rate(from_code, to_code)
    if result is None:
        return f"Could not fetch exchange rate for {from_code} → {to_code}"

    rate, date_str = result
    converted = amount * rate
    date_note = f", ECB {date_str}" if date_str else ""
    return (
        f"{amount:.2f} {from_code} = {converted:.2f} {to_code}"
        f" (rate: {rate:.4f}{date_note})"
    )


def _handle_currency_query(query: str) -> str | None:
    """Parse a natural-language currency query and convert.

    Args:
        query: Raw user query, e.g. ``"convert 100 USD to EUR"``.

    Returns:
        A conversion result string, or ``None`` if the query could not
        be parsed (orchestrator falls back to LLM).
    """
    match = _QUERY_RE.search(query)
    if not match:
        return None

    amount_str = match.group(1).replace(",", "")
    from_token = match.group(2).strip()
    to_token = match.group(3).strip()

    try:
        amount = float(amount_str)
    except ValueError:
        return None

    from_code = _resolve_code(from_token)
    to_code = _resolve_code(to_token)

    if from_code is None or to_code is None:
        return None

    return convert_currency(amount, from_code, to_code)


REGISTRY.register(
    ToolDefinition(
        name="currency",
        router_tier="currency",
        label="Tool: currency",
        description=(
            "currency conversion between major world currencies "
            "(USD, EUR, GBP, JPY, CAD, AUD and 24 more)"
        ),
        examples=[
            "convert 100 USD to EUR",
            "100 dollars to pounds",
            "how much is 50 GBP in Japanese yen",
            "1000 JPY in USD",
        ],
        default_enabled=True,
        min_tier="trivial_llm",
        approach="A",
        callable=_handle_currency_query,
        category="web",
    )
)
