"""Paper trading engine for simulated trading."""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from trading_bot.models import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Portfolio,
    Position,
)


class PaperTrader:
    """Simulated trading engine that tracks virtual positions and PnL."""

    def __init__(
        self, initial_balance: float = 10000.0, state_file: str = "paper_trading_state.json"
    ) -> None:
        self.state_file = Path(state_file)
        self.portfolio = Portfolio(
            balance=initial_balance,
            initial_balance=initial_balance,
        )
        self.order_history: list[Order] = []
        self._load_state()

    def _load_state(self) -> None:
        """Load saved state from disk if available."""
        if self.state_file.exists():
            content = self.state_file.read_text().strip()
            if not content:
                return
            data = json.loads(content)
            self.portfolio = Portfolio(**data["portfolio"])
            self.order_history = [Order(**o) for o in data.get("order_history", [])]

    def _save_state(self) -> None:
        """Persist state to disk."""
        data = {
            "portfolio": self.portfolio.model_dump(mode="json"),
            "order_history": [o.model_dump(mode="json") for o in self.order_history],
        }
        self.state_file.write_text(json.dumps(data, indent=2, default=str))

    def execute_order(self, symbol: str, side: OrderSide, amount: float, price: float) -> Order:
        """Execute a simulated order at the given price."""
        order = Order(
            id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            amount=amount,
            price=price,
        )

        if side == OrderSide.BUY:
            cost = amount * price
            if cost > self.portfolio.balance:
                order.status = OrderStatus.FAILED
                self.order_history.append(order)
                self._save_state()
                return order

            self.portfolio.balance -= cost
            if symbol in self.portfolio.positions:
                pos = self.portfolio.positions[symbol]
                total_amount = pos.amount + amount
                avg_price = (
                    (pos.entry_price * pos.amount + price * amount) / total_amount
                )
                pos.amount = total_amount
                pos.entry_price = avg_price
                pos.current_price = price
            else:
                self.portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    amount=amount,
                    entry_price=price,
                    current_price=price,
                )

        elif side == OrderSide.SELL:
            if symbol not in self.portfolio.positions:
                order.status = OrderStatus.FAILED
                self.order_history.append(order)
                self._save_state()
                return order

            pos = self.portfolio.positions[symbol]
            if amount > pos.amount:
                amount = pos.amount

            revenue = amount * price
            pnl = (price - pos.entry_price) * amount

            self.portfolio.balance += revenue
            self.portfolio.total_pnl += pnl
            self.portfolio.total_trades += 1

            if pnl > 0:
                self.portfolio.winning_trades += 1
            else:
                self.portfolio.losing_trades += 1

            pos.amount -= amount
            if pos.amount <= 0.000001:
                del self.portfolio.positions[symbol]
            else:
                pos.current_price = price

        order.status = OrderStatus.FILLED
        order.filled_price = price
        order.filled_at = datetime.now(UTC)
        self.order_history.append(order)
        self._save_state()
        return order

    def update_prices(self, prices: dict[str, float]) -> None:
        """Update current prices for open positions."""
        for symbol, price in prices.items():
            if symbol in self.portfolio.positions:
                pos = self.portfolio.positions[symbol]
                pos.current_price = price
                pos.unrealized_pnl = (price - pos.entry_price) * pos.amount
        self._save_state()

    def get_portfolio(self) -> Portfolio:
        """Get current portfolio state."""
        return self.portfolio

    def reset(self) -> None:
        """Reset paper trading to initial state."""
        self.portfolio = Portfolio(
            balance=self.portfolio.initial_balance,
            initial_balance=self.portfolio.initial_balance,
        )
        self.order_history = []
        self._save_state()
