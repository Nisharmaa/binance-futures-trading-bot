"""
orders.py — Backend logic for Binance Futures Testnet Trading Bot
-----------------------------------------------------------------
This module handles order placement and validation against the
Binance Futures Testnet REST API.

To use with real Testnet credentials:
  1. Sign up at https://testnet.binancefuture.com
  2. Generate API Key & Secret
  3. Set them in your .env file or Streamlit secrets
"""
import logging
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

logging.basicConfig(
    filename="logs/trading.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ── Testnet base URL ──────────────────────────────────────────────────────────
TESTNET_BASE_URL = "https://testnet.binancefuture.com"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _sign(query_string: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature required by Binance API."""
    return hmac.new(
        secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _build_headers(api_key: str) -> dict:
    """Return the request headers with the API key."""
    return {
        "X-MBX-APIKEY": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }


# ── Validation ────────────────────────────────────────────────────────────────

def validate_order(symbol: str, side: str, order_type: str,
                   quantity: float, price: float | None) -> tuple[bool, str]:
    """
    Validate order inputs before sending to the API.

    Returns:
        (is_valid: bool, message: str)
    """
    if not symbol or not symbol.strip():
        return False, "Symbol cannot be empty."

    if side not in ("BUY", "SELL"):
        return False, f"Invalid side '{side}'. Must be BUY or SELL."

    if order_type not in ("MARKET", "LIMIT"):
        return False, f"Invalid order type '{order_type}'."

    if quantity is None or quantity <= 0:
        return False, "Quantity must be a positive number."

    if order_type == "LIMIT":
        if price is None or price <= 0:
            return False, "Price must be a positive number for LIMIT orders."

    return True, "Validation passed."


# ── Mock order (no real credentials needed for demo/UI testing) ───────────────

def place_order_mock(symbol: str, side: str, order_type: str,
                     quantity: float, price: float | None) -> dict:
    """
    Simulate a successful order response without hitting any API.
    Useful for UI development and demos.

    Returns a dict that mirrors the real Binance Futures order response shape.
    """
    order_id = int(time.time() * 1000) % 10_000_000  # fake numeric ID

    response = {
        "orderId": order_id,
        "symbol": symbol.upper(),
        "status": "FILLED" if order_type == "MARKET" else "NEW",
        "clientOrderId": f"bot_{order_id}",
        "price": str(price) if price else "0",
        "avgPrice": str(price) if price else "43250.00",  # simulated fill price
        "origQty": str(quantity),
        "executedQty": str(quantity) if order_type == "MARKET" else "0",
        "type": order_type,
        "side": side,
        "timeInForce": "GTC" if order_type == "LIMIT" else "IOC",
        "transactTime": int(time.time() * 1000),
        "_source": "mock",  # flag so the UI can show a disclaimer
    }
    return response


# ── Real Testnet order ────────────────────────────────────────────────────────

def place_order_live(api_key: str, api_secret: str,
                     symbol: str, side: str, order_type: str,
                     quantity: float, price: float | None,
                     time_in_force: str = "GTC") -> dict:
    """
    Place a real order on the Binance Futures Testnet.

    Args:
        api_key:       Your Testnet API key.
        api_secret:    Your Testnet API secret.
        symbol:        Trading pair, e.g. "BTCUSDT".
        side:          "BUY" or "SELL".
        order_type:    "MARKET" or "LIMIT".
        quantity:      Order size in base asset units.
        price:         Limit price (required for LIMIT orders).
        time_in_force: "GTC", "IOC", or "FOK" (LIMIT only).

    Returns:
        Parsed JSON response from the Binance API.

    Raises:
        ValueError:   On API-level errors (bad request, auth failure, etc.).
        RuntimeError: On network / connectivity errors.
    """
    endpoint = "/fapi/v1/order"
    url = TESTNET_BASE_URL + endpoint

    # Build the parameter dict
    params: dict = {
        "symbol": symbol.upper(),
        "side": side,
        "type": order_type,
        "quantity": quantity,
        "timestamp": int(time.time() * 1000),
    }

    if order_type == "LIMIT":
        params["price"] = price
        params["timeInForce"] = time_in_force

    # Sign the request
    query_string = urlencode(params)
    params["signature"] = _sign(query_string, api_secret)

    try:
        logging.info(f"Sending {side} {order_type} order for {symbol}")
        resp = requests.post(url, headers=_build_headers(api_key),
                             params=params, timeout=10)
        data = resp.json()

        # Binance returns an error code on failure
        if "code" in data and data["code"] != 200:
            raise ValueError(f"Binance API error {data['code']}: {data.get('msg', 'Unknown error')}")
        logging.info(f"Order success: {data}")

        return data

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Network error while contacting Binance Testnet: {exc}") from exc


# ── Account balance helper ────────────────────────────────────────────────────

def get_account_balance_mock() -> list[dict]:
    """Return simulated USDT balance for display in the UI."""
    return [
        {"asset": "USDT",  "balance": "10000.00", "availableBalance": "9850.00"},
        {"asset": "BTC",   "balance": "0.25",     "availableBalance": "0.25"},
    ]
