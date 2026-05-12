"""Configuration management for the trading bot."""

from pydantic import Field
from pydantic_settings import BaseSettings

from trading_bot.models import TradingMode


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic
    anthropic_api_key: str = ""
    analysis_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096

    # Coinbase
    coinbase_api_key: str = ""
    coinbase_api_secret: str = ""

    # Trading
    trading_mode: TradingMode = TradingMode.PAPER
    default_quote_currency: str = "USDT"
    paper_trading_balance: float = 10000.0

    # Symbols to track
    trading_symbols: list[str] = Field(
        default=["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"]
    )

    # Risk management
    max_position_size_pct: float = 0.1
    max_open_positions: int = 5
    min_confidence: float = 0.6

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def load_settings() -> Settings:
    """Load and validate settings."""
    return Settings()
