"""Tests for data models."""

from trading_bot.models import (
    AnalysisReport,
    MarketData,
    Order,
    OrderSide,
    OrderType,
    Portfolio,
    Position,
    SignalStrength,
    TradeRecommendation,
)


def test_market_data_creation() -> None:
    data = MarketData(
        symbol="BTC/USDT",
        current_price=50000.0,
        change_24h=2.5,
        volume_24h=1000000.0,
        high_24h=51000.0,
        low_24h=49000.0,
    )
    assert data.symbol == "BTC/USDT"
    assert data.current_price == 50000.0


def test_trade_recommendation() -> None:
    rec = TradeRecommendation(
        symbol="BTC/USDT",
        signal=SignalStrength.BUY,
        confidence=0.8,
        entry_price=50000.0,
        stop_loss=48000.0,
        take_profit=55000.0,
    )
    assert rec.confidence == 0.8
    assert rec.signal == SignalStrength.BUY


def test_order() -> None:
    order = Order(
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        amount=0.1,
    )
    assert order.side == OrderSide.BUY
    assert order.amount == 0.1


def test_portfolio_return_pct() -> None:
    portfolio = Portfolio(
        balance=11000.0,
        initial_balance=10000.0,
    )
    assert portfolio.return_pct == 10.0


def test_portfolio_return_pct_with_positions() -> None:
    portfolio = Portfolio(
        balance=5000.0,
        initial_balance=10000.0,
        positions={
            "BTC/USDT": Position(
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                amount=0.1,
                entry_price=50000.0,
                current_price=60000.0,
            )
        },
    )
    assert portfolio.total_value == 11000.0
    assert portfolio.return_pct == 10.0


def test_analysis_report() -> None:
    report = AnalysisReport(
        market_summary="Test summary",
        recommendations=[
            TradeRecommendation(
                symbol="BTC/USDT",
                signal=SignalStrength.BUY,
                confidence=0.8,
            )
        ],
        risk_assessment="Low risk",
        raw_analysis="{}",
    )
    assert len(report.recommendations) == 1
    assert report.market_summary == "Test summary"
