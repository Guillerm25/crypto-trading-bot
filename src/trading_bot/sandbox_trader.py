"""Sandbox trading via Bybit Testnet API."""

import uuid
from datetime import UTC, datetime

import ccxt

from trading_bot.config import Settings
from trading_bot.models import Order, OrderSide, OrderStatus, OrderType


class SandboxTrader:
    """Executes real orders against the Bybit Testnet."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        config: dict[str, object] = {
            "enableRateLimit": True,
            "apiKey": settings.bybit_testnet_api_key,
            "secret": settings.bybit_testnet_api_secret,
            "hostname": settings.bybit_hostname,
        }
        self.exchange = ccxt.bybit(config)
        self.exchange.set_sandbox_mode(True)

    def execute_order(
        self, symbol: str, side: OrderSide, amount: float, price: float
    ) -> Order:
        """Place an order on the Bybit Testnet."""
        order = Order(
            id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            amount=amount,
            price=price,
        )

        try:
            result = self.exchange.create_order(
                symbol=symbol,
                type="market",
                side=side.value,
                amount=amount,
            )
            order.id = str(result.get("id", order.id))
            order.status = OrderStatus.FILLED
            order.filled_price = float(result.get("average", price) or price)
            order.filled_at = datetime.now(UTC)
        except ccxt.InsufficientFunds:
            order.status = OrderStatus.FAILED
        except ccxt.BaseError as exc:
            order.status = OrderStatus.FAILED
            order.id = f"ERR-{order.id}"
            raise RuntimeError(f"Testnet order failed: {exc}") from exc

        return order

    def validate_credentials(self) -> tuple[bool, str]:
        """Validate testnet API credentials. Returns (ok, message)."""
        try:
            self.exchange.fetch_balance()
            return True, "Credentials valid"
        except ccxt.AuthenticationError as exc:
            return False, f"Invalid API key: {exc}"
        except ccxt.BaseError as exc:
            return False, f"Connection error: {exc}"

    def fetch_balance(self) -> dict[str, float]:
        """Fetch current testnet account balances."""
        balance = self.exchange.fetch_balance()
        result: dict[str, float] = {}
        for currency, data in balance.get("total", {}).items():
            if data and float(data) > 0:
                result[currency] = float(data)
        return result

    def fetch_open_orders(self, symbol: str | None = None) -> list[dict[str, object]]:
        """Fetch open orders from testnet."""
        return self.exchange.fetch_open_orders(symbol)
