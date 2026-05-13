"""Main CLI entrypoint for the crypto trading bot."""

import sys

import click
from rich.console import Console

from trading_bot.config import load_settings
from trading_bot.dashboard import (
    display_analysis_report,
    display_executed_orders,
    display_market_data,
    display_portfolio,
)
from trading_bot.executor import TradeExecutor
from trading_bot.market_data import MarketDataFetcher
from trading_bot.models import TradingMode
from trading_bot.paper_trader import PaperTrader
from trading_bot.sandbox_trader import SandboxTrader
from trading_bot.text_parser import parse_analysis_text

console = Console()


@click.group()
def cli() -> None:
    """Crypto Trading Bot - Paste your analysis and execute trades."""
    pass


@cli.command()
def status() -> None:
    """Show current portfolio status and open positions."""
    settings = load_settings()
    paper_trader = PaperTrader(initial_balance=settings.paper_trading_balance)
    market_data = MarketDataFetcher(settings)

    portfolio = paper_trader.get_portfolio()

    if portfolio.positions:
        prices: dict[str, float] = {}
        for symbol in portfolio.positions:
            try:
                ticker = market_data.fetch_ticker(symbol)
                prices[symbol] = ticker.current_price
            except Exception:
                pass
        paper_trader.update_prices(prices)
        portfolio = paper_trader.get_portfolio()

    display_portfolio(portfolio)


@cli.command()
@click.option("--symbols", "-s", help="Comma-separated symbols (e.g., BTC/USDT,ETH/USDT)")
def market(symbols: str | None) -> None:
    """Fetch and display current market data."""
    settings = load_settings()
    fetcher = MarketDataFetcher(settings)

    symbol_list = symbols.split(",") if symbols else settings.trading_symbols
    console.print(f"[bold]Fetching market data for {len(symbol_list)} symbols...[/bold]\n")

    data = fetcher.fetch_multiple(symbol_list)
    display_market_data(data)


@cli.command()
@click.option(
    "--file", "-f", "file_path",
    type=click.Path(exists=True),
    help="Read analysis from a file",
)
@click.option("--auto-execute/--no-auto-execute", default=False, help="Auto-execute trades")
def execute(file_path: str | None, auto_execute: bool) -> None:
    """Parse pasted analysis text and execute trades.

    Paste your analysis from ChatGPT or any source. The bot will detect
    symbols (BTC, ETH, SOL...), buy/sell signals, entry prices, stop-loss,
    and take-profit levels from the text.

    Usage:
      trading-bot execute                   # Interactive: paste text, then Ctrl+D
      trading-bot execute -f analysis.txt   # Read from file
      trading-bot execute --auto-execute    # Auto-execute detected trades
    """
    settings = load_settings()

    if file_path:
        with open(file_path) as f:
            analysis_text = f.read()
    else:
        console.print(
            "[bold cyan]Paste your analysis below (press Ctrl+D when done):[/bold cyan]\n"
        )
        analysis_text = sys.stdin.read()

    if not analysis_text.strip():
        console.print("[red]Error: No analysis text provided.[/red]")
        raise SystemExit(1)

    console.print(f"\n[bold]Parsing analysis ({len(analysis_text)} characters)...[/bold]\n")
    report = parse_analysis_text(analysis_text, settings.default_quote_currency)
    display_analysis_report(report)

    if not report.recommendations:
        console.print(
            "[yellow]No trade signals detected in the text. "
            "Make sure it contains buy/sell recommendations for known symbols "
            "(BTC, ETH, SOL, etc.).[/yellow]"
        )
        return

    if auto_execute:
        fetcher = MarketDataFetcher(settings)
        paper_trader = PaperTrader(initial_balance=settings.paper_trading_balance)

        sandbox_trader = None
        if settings.trading_mode == TradingMode.SANDBOX:
            if not settings.bybit_testnet_api_key:
                console.print(
                    "[red]Error: Sandbox mode requires BYBIT_TESTNET_API_KEY "
                    "and BYBIT_TESTNET_API_SECRET.\n"
                    "Create testnet credentials at: "
                    "https://testnet.bybit.com[/red]"
                )
                raise SystemExit(1)
            sandbox_trader = SandboxTrader(settings)
            console.print(
                "[bold magenta]Mode: SANDBOX — orders sent to Bybit "
                "Testnet (demo wallet)[/bold magenta]\n"
            )

        executor = TradeExecutor(settings, fetcher, paper_trader, sandbox_trader)

        console.print("[bold]Executing recommendations...[/bold]\n")
        orders = executor.execute_recommendations(report)
        display_executed_orders(orders)

        if settings.trading_mode == TradingMode.SANDBOX and sandbox_trader:
            console.print("[bold]Sandbox Account Balances:[/bold]")
            try:
                balances = sandbox_trader.fetch_balance()
                for currency, amount in sorted(balances.items()):
                    console.print(f"  {currency}: {amount:,.8f}")
            except Exception as exc:
                console.print(f"  [yellow]Could not fetch balances: {exc}[/yellow]")
        else:
            console.print("[bold]Portfolio Status:[/bold]")
            prices: dict[str, float] = {}
            for rec in report.recommendations:
                try:
                    ticker = fetcher.fetch_ticker(rec.symbol)
                    prices[rec.symbol] = ticker.current_price
                except Exception:
                    pass
            paper_trader.update_prices(prices)
            display_portfolio(paper_trader.get_portfolio())
    else:
        console.print(
            "[yellow]Run with --auto-execute to execute trades based on "
            "these recommendations.[/yellow]\n"
        )


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to reset paper trading?")
def reset() -> None:
    """Reset paper trading portfolio to initial state."""
    settings = load_settings()
    paper_trader = PaperTrader(initial_balance=settings.paper_trading_balance)
    paper_trader.reset()
    console.print("[green]Paper trading portfolio has been reset.[/green]")


if __name__ == "__main__":
    cli()
