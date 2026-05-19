"""Data models for the trading bot."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TradingMode(StrEnum):
    PAPER = "paper"
    SANDBOX = "sandbox"
    LIVE = "live"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(StrEnum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class SignalStrength(StrEnum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class OHLCV(BaseModel):
    """Single candlestick data point."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketData(BaseModel):
    """Market data for a trading pair."""

    symbol: str
    current_price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    candles: list[OHLCV] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TradeRecommendation(BaseModel):
    """AI-generated trade recommendation."""

    symbol: str
    signal: SignalStrength
    confidence: float = Field(ge=0, le=1)
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size_pct: float = Field(default=0.05, ge=0, le=1)
    reasoning: str = ""


class AnalysisReport(BaseModel):
    """Full AI analysis report."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    market_summary: str
    recommendations: list[TradeRecommendation]
    risk_assessment: str
    raw_analysis: str


class Order(BaseModel):
    """Trade order."""

    id: str = ""
    symbol: str
    side: OrderSide
    order_type: OrderType = OrderType.MARKET
    amount: float
    price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    filled_price: float | None = None
    filled_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Position(BaseModel):
    """Open position."""

    symbol: str
    side: OrderSide
    amount: float
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    opened_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Portfolio(BaseModel):
    """Portfolio state."""

    balance: float
    initial_balance: float
    positions: dict[str, Position] = Field(default_factory=dict)
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0

    @property
    def total_value(self) -> float:
        positions_value = sum(p.amount * p.current_price for p in self.positions.values())
        return self.balance + positions_value

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades

    @property
    def return_pct(self) -> float:
        if self.initial_balance == 0:
            return 0.0
        return ((self.total_value - self.initial_balance) / self.initial_balance) * 100
