"""Market data fetching from Bybit via ccxt."""

from datetime import UTC, datetime

import ccxt

from trading_bot.config import Settings
from trading_bot.models import OHLCV, MarketData, TradingMode


class MarketDataFetcher:
    """Fetches market data from Bybit using ccxt."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.is_sandbox = settings.trading_mode == TradingMode.SANDBOX

        exchange_config: dict[str, object] = {
            "enableRateLimit": True,
            "hostname": settings.bybit_hostname,
        }
        self.exchange = ccxt.bybit(exchange_config)
        if self.is_sandbox:
            self.exchange.set_sandbox_mode(True)

    def fetch_ticker(self, symbol: str) -> MarketData:
        """Fetch current ticker data for a symbol."""
        ticker = self.exchange.fetch_ticker(symbol)

        return MarketData(
            symbol=symbol,
            current_price=float(ticker.get("last", 0) or 0),
            change_24h=float(ticker.get("percentage", 0) or 0),
            volume_24h=float(ticker.get("quoteVolume", 0) or 0),
            high_24h=float(ticker.get("high", 0) or 0),
            low_24h=float(ticker.get("low", 0) or 0),
        )

    def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1h", limit: int = 48
    ) -> list[OHLCV]:
        """Fetch OHLCV candlestick data."""
        raw_candles = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

        candles: list[OHLCV] = []
        for candle in raw_candles:
            candles.append(
                OHLCV(
                    timestamp=datetime.fromtimestamp(candle[0] / 1000, tz=UTC),
                    open=float(candle[1]),
                    high=float(candle[2]),
                    low=float(candle[3]),
                    close=float(candle[4]),
                    volume=float(candle[5]),
                )
            )
        return candles

    def fetch_full_market_data(self, symbol: str, timeframe: str = "1h") -> MarketData:
        """Fetch ticker + OHLCV data for a symbol."""
        market_data = self.fetch_ticker(symbol)
        market_data.candles = self.fetch_ohlcv(symbol, timeframe=timeframe)
        return market_data

    def fetch_multiple(self, symbols: list[str]) -> list[MarketData]:
        """Fetch market data for multiple symbols."""
        results: list[MarketData] = []
        for symbol in symbols:
            try:
                data = self.fetch_full_market_data(symbol)
                results.append(data)
            except ccxt.BaseError as e:
                print(f"Error fetching {symbol}: {e}")
        return results

    def get_available_symbols(self) -> list[str]:
        """Get list of available trading pairs."""
        self.exchange.load_markets()
        return [
            symbol
            for symbol in self.exchange.symbols
            if symbol.endswith(f"/{self.settings.default_quote_currency}")
        ]
