"""Configuration management for the trading bot."""

from pydantic import Field
from pydantic_settings import BaseSettings

from trading_bot.models import TradingMode


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Bybit API (production / market data)
    bybit_api_key: str = ""
    bybit_api_secret: str = ""

    # Bybit Testnet (demo wallet)
    bybit_testnet_api_key: str = ""
    bybit_testnet_api_secret: str = ""

    # Bybit hostname (use bybit.eu for Europe, bybit.com for global)
    bybit_hostname: str = "bybit.com"

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
