"""Sandbox trading via Coinbase Exchange Sandbox API."""

import uuid
from datetime import UTC, datetime

import ccxt

from trading_bot.config import Settings
from trading_bot.models import Order, OrderSide, OrderStatus, OrderType


class SandboxTrader:
    """Executes real orders against the Coinbase Exchange Sandbox."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        config: dict[str, object] = {
            "enableRateLimit": True,
            "apiKey": settings.coinbase_sandbox_api_key,
            "secret": settings.coinbase_sandbox_api_secret,
            "password": settings.coinbase_sandbox_passphrase,
        }
        self.exchange = ccxt.coinbaseexchange(config)
        self.exchange.set_sandbox_mode(True)

    def execute_order(
        self, symbol: str, side: OrderSide, amount: float, price: float
    ) -> Order:
        """Place an order on the Coinbase Exchange Sandbox."""
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
            raise RuntimeError(f"Sandbox order failed: {exc}") from exc

        return order

    def fetch_balance(self) -> dict[str, float]:
        """Fetch current sandbox account balances."""
        balance = self.exchange.fetch_balance()
        result: dict[str, float] = {}
        for currency, data in balance.get("total", {}).items():
            if data and float(data) > 0:
                result[currency] = float(data)
        return result

    def fetch_open_orders(self, symbol: str | None = None) -> list[dict[str, object]]:
        """Fetch open orders from sandbox."""
        return self.exchange.fetch_open_orders(symbol)
