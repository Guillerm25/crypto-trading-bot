"""Order execution module - routes orders to paper or live trading."""

from rich.console import Console

from trading_bot.config import Settings
from trading_bot.market_data import MarketDataFetcher
from trading_bot.models import (
    AnalysisReport,
    Order,
    OrderSide,
    Portfolio,
    SignalStrength,
    TradingMode,
)
from trading_bot.paper_trader import PaperTrader

console = Console()


class TradeExecutor:
    """Executes trades based on AI recommendations."""

    def __init__(
        self,
        settings: Settings,
        market_data: MarketDataFetcher,
        paper_trader: PaperTrader,
    ) -> None:
        self.settings = settings
        self.market_data = market_data
        self.paper_trader = paper_trader

    def execute_recommendations(self, report: AnalysisReport) -> list[Order]:
        """Execute actionable recommendations from the AI analysis."""
        executed_orders: list[Order] = []
        portfolio = self.paper_trader.get_portfolio()

        for rec in report.recommendations:
            if rec.confidence < self.settings.min_confidence:
                console.print(
                    f"  [dim]Skipping {rec.symbol}: confidence {rec.confidence:.0%} "
                    f"< minimum {self.settings.min_confidence:.0%}[/dim]"
                )
                continue

            if rec.signal in (SignalStrength.HOLD,):
                continue

            if rec.signal in (SignalStrength.BUY, SignalStrength.STRONG_BUY):
                order = self._execute_buy(rec.symbol, rec.position_size_pct, portfolio)
            elif rec.signal in (SignalStrength.SELL, SignalStrength.STRONG_SELL):
                order = self._execute_sell(rec.symbol)
            else:
                continue

            if order is not None:
                executed_orders.append(order)

        return executed_orders

    def _execute_buy(
        self, symbol: str, size_pct: float, portfolio: Portfolio
    ) -> Order | None:
        """Execute a buy order."""
        if self.settings.trading_mode == TradingMode.LIVE:
            console.print("[bold red]⚠ Live trading not enabled yet. Use paper mode.[/bold red]")
            return None

        open_positions = len(portfolio.positions)
        if open_positions >= self.settings.max_open_positions:
            max_pos = self.settings.max_open_positions
            console.print(f"  [yellow]Max open positions ({max_pos}) reached[/yellow]")
            return None

        if symbol in portfolio.positions:
            console.print(f"  [yellow]Already have position in {symbol}[/yellow]")
            return None

        size_pct = min(size_pct, self.settings.max_position_size_pct)
        budget = portfolio.balance * size_pct

        ticker = self.market_data.fetch_ticker(symbol)
        price = ticker.current_price
        if price <= 0:
            return None

        amount = budget / price

        order = self.paper_trader.execute_order(symbol, OrderSide.BUY, amount, price)
        console.print(
            f"  [green]BUY {symbol}: {amount:.6f} @ ${price:,.2f} "
            f"(${budget:,.2f})[/green]"
        )
        return order

    def _execute_sell(self, symbol: str) -> Order | None:
        """Execute a sell order for an existing position."""
        if self.settings.trading_mode == TradingMode.LIVE:
            console.print("[bold red]⚠ Live trading not enabled yet. Use paper mode.[/bold red]")
            return None

        portfolio = self.paper_trader.get_portfolio()
        if symbol not in portfolio.positions:
            return None

        position = portfolio.positions[symbol]
        sell_amount = position.amount
        sell_entry = position.entry_price
        ticker = self.market_data.fetch_ticker(symbol)
        price = ticker.current_price

        order = self.paper_trader.execute_order(symbol, OrderSide.SELL, sell_amount, price)
        pnl = (price - sell_entry) * sell_amount
        color = "green" if pnl >= 0 else "red"
        console.print(
            f"  [{color}]SELL {symbol}: {sell_amount:.6f} @ ${price:,.2f} "
            f"(PnL: ${pnl:,.2f})[/{color}]"
        )
        return order
