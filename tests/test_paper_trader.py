"""Tests for the paper trading engine."""

import tempfile
from pathlib import Path

from trading_bot.models import OrderSide, OrderStatus
from trading_bot.paper_trader import PaperTrader


def _make_trader(balance: float = 10000.0) -> PaperTrader:
    """Create a paper trader with a temporary state file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    trader = PaperTrader(initial_balance=balance, state_file=tmp.name)
    return trader


def test_initial_portfolio() -> None:
    trader = _make_trader()
    portfolio = trader.get_portfolio()
    assert portfolio.balance == 10000.0
    assert portfolio.initial_balance == 10000.0
    assert len(portfolio.positions) == 0
    assert portfolio.total_trades == 0


def test_buy_order() -> None:
    trader = _make_trader()
    order = trader.execute_order("BTC/USDT", OrderSide.BUY, 0.1, 50000.0)
    assert order.status == OrderStatus.FILLED
    assert order.filled_price == 50000.0

    portfolio = trader.get_portfolio()
    assert portfolio.balance == 5000.0
    assert "BTC/USDT" in portfolio.positions
    assert portfolio.positions["BTC/USDT"].amount == 0.1


def test_sell_order() -> None:
    trader = _make_trader()
    trader.execute_order("BTC/USDT", OrderSide.BUY, 0.1, 50000.0)
    order = trader.execute_order("BTC/USDT", OrderSide.SELL, 0.1, 55000.0)

    assert order.status == OrderStatus.FILLED
    portfolio = trader.get_portfolio()
    assert "BTC/USDT" not in portfolio.positions
    assert portfolio.total_trades == 1
    assert portfolio.winning_trades == 1
    assert portfolio.total_pnl == 500.0


def test_sell_losing_trade() -> None:
    trader = _make_trader()
    trader.execute_order("ETH/USDT", OrderSide.BUY, 1.0, 3000.0)
    order = trader.execute_order("ETH/USDT", OrderSide.SELL, 1.0, 2800.0)

    assert order.status == OrderStatus.FILLED
    portfolio = trader.get_portfolio()
    assert portfolio.losing_trades == 1
    assert portfolio.total_pnl == -200.0


def test_buy_insufficient_funds() -> None:
    trader = _make_trader(balance=100.0)
    order = trader.execute_order("BTC/USDT", OrderSide.BUY, 1.0, 50000.0)
    assert order.status == OrderStatus.FAILED


def test_sell_no_position() -> None:
    trader = _make_trader()
    order = trader.execute_order("BTC/USDT", OrderSide.SELL, 0.1, 50000.0)
    assert order.status == OrderStatus.FAILED


def test_state_persistence() -> None:
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    trader = PaperTrader(initial_balance=10000.0, state_file=tmp.name)
    trader.execute_order("BTC/USDT", OrderSide.BUY, 0.1, 50000.0)

    trader2 = PaperTrader(initial_balance=10000.0, state_file=tmp.name)
    portfolio = trader2.get_portfolio()
    assert portfolio.balance == 5000.0
    assert "BTC/USDT" in portfolio.positions

    Path(tmp.name).unlink(missing_ok=True)


def test_update_prices() -> None:
    trader = _make_trader()
    trader.execute_order("BTC/USDT", OrderSide.BUY, 0.1, 50000.0)
    trader.update_prices({"BTC/USDT": 55000.0})

    portfolio = trader.get_portfolio()
    pos = portfolio.positions["BTC/USDT"]
    assert pos.current_price == 55000.0
    assert pos.unrealized_pnl == 500.0


def test_reset() -> None:
    trader = _make_trader()
    trader.execute_order("BTC/USDT", OrderSide.BUY, 0.1, 50000.0)
    trader.reset()

    portfolio = trader.get_portfolio()
    assert portfolio.balance == 10000.0
    assert len(portfolio.positions) == 0
    assert portfolio.total_trades == 0


def test_portfolio_total_value() -> None:
    trader = _make_trader(balance=10000.0)
    trader.execute_order("BTC/USDT", OrderSide.BUY, 0.1, 50000.0)
    trader.update_prices({"BTC/USDT": 60000.0})

    portfolio = trader.get_portfolio()
    assert portfolio.total_value == 5000.0 + 0.1 * 60000.0


def test_win_rate() -> None:
    trader = _make_trader(balance=100000.0)
    trader.execute_order("BTC/USDT", OrderSide.BUY, 0.1, 50000.0)
    trader.execute_order("BTC/USDT", OrderSide.SELL, 0.1, 55000.0)
    trader.execute_order("ETH/USDT", OrderSide.BUY, 1.0, 3000.0)
    trader.execute_order("ETH/USDT", OrderSide.SELL, 1.0, 2500.0)

    portfolio = trader.get_portfolio()
    assert portfolio.win_rate == 0.5
