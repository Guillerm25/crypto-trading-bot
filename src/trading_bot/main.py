"""Main CLI entrypoint for the crypto trading bot."""

import time

import click
from rich.console import Console

from trading_bot.ai_analyst import AIAnalyst
from trading_bot.config import load_settings
from trading_bot.dashboard import (
    display_analysis_report,
    display_executed_orders,
    display_market_data,
    display_portfolio,
)
from trading_bot.executor import TradeExecutor
from trading_bot.market_data import MarketDataFetcher
from trading_bot.paper_trader import PaperTrader

console = Console()


@click.group()
def cli() -> None:
    """Crypto Trading Bot - AI-powered automated trading."""
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
@click.option("--symbols", "-s", help="Comma-separated symbols to analyze")
def analyze(symbols: str | None) -> None:
    """Run AI analysis on market data and display recommendations."""
    settings = load_settings()

    if not settings.openai_api_key:
        console.print("[bold red]Error: OPENAI_API_KEY not set. Add it to .env[/bold red]")
        raise SystemExit(1)

    fetcher = MarketDataFetcher(settings)
    analyst = AIAnalyst(settings)

    symbol_list = symbols.split(",") if symbols else settings.trading_symbols
    console.print(f"[bold]Fetching market data for {len(symbol_list)} symbols...[/bold]\n")
    market_data_list = fetcher.fetch_multiple(symbol_list)

    if not market_data_list:
        console.print("[red]No market data available. Check your connection.[/red]")
        raise SystemExit(1)

    display_market_data(market_data_list)

    console.print("[bold]Running AI analysis with ChatGPT...[/bold]\n")
    report = analyst.analyze(market_data_list)
    display_analysis_report(report)


@cli.command()
@click.option("--symbols", "-s", help="Comma-separated symbols to trade")
@click.option("--auto-execute/--no-auto-execute", default=False, help="Auto-execute")
def trade(symbols: str | None, auto_execute: bool) -> None:
    """Run full trading cycle: fetch data, analyze, and optionally execute."""
    settings = load_settings()

    if not settings.openai_api_key:
        console.print("[bold red]Error: OPENAI_API_KEY not set. Add it to .env[/bold red]")
        raise SystemExit(1)

    fetcher = MarketDataFetcher(settings)
    analyst = AIAnalyst(settings)
    paper_trader = PaperTrader(initial_balance=settings.paper_trading_balance)
    executor = TradeExecutor(settings, fetcher, paper_trader)

    symbol_list = symbols.split(",") if symbols else settings.trading_symbols

    console.print(
        f"[bold cyan]Trading Bot - Mode: {settings.trading_mode.value.upper()}[/bold cyan]\n"
    )

    # Step 1: Fetch market data
    console.print("[bold]Step 1: Fetching market data...[/bold]")
    market_data_list = fetcher.fetch_multiple(symbol_list)

    if not market_data_list:
        console.print("[red]No market data available.[/red]")
        raise SystemExit(1)

    display_market_data(market_data_list)

    # Step 2: AI Analysis
    console.print("[bold]Step 2: Running AI analysis with ChatGPT...[/bold]\n")
    report = analyst.analyze(market_data_list)
    display_analysis_report(report)

    # Step 3: Execute trades
    if auto_execute:
        console.print("[bold]Step 3: Executing recommendations...[/bold]\n")
        orders = executor.execute_recommendations(report)
        display_executed_orders(orders)
    else:
        console.print(
            "[yellow]Auto-execute disabled. Run with --auto-execute to trade.[/yellow]\n"
        )

    # Step 4: Show portfolio
    console.print("[bold]Portfolio Status:[/bold]")
    prices = {d.symbol: d.current_price for d in market_data_list}
    paper_trader.update_prices(prices)
    display_portfolio(paper_trader.get_portfolio())


@cli.command()
@click.option("--symbols", "-s", help="Comma-separated symbols to trade")
@click.option("--interval", "-i", default=3600, help="Interval between cycles in seconds")
def run(symbols: str | None, interval: int) -> None:
    """Run the trading bot continuously."""
    settings = load_settings()

    if not settings.openai_api_key:
        console.print("[bold red]Error: OPENAI_API_KEY not set. Add it to .env[/bold red]")
        raise SystemExit(1)

    fetcher = MarketDataFetcher(settings)
    analyst = AIAnalyst(settings)
    paper_trader = PaperTrader(initial_balance=settings.paper_trading_balance)
    executor = TradeExecutor(settings, fetcher, paper_trader)

    symbol_list = symbols.split(",") if symbols else settings.trading_symbols

    console.print(
        f"[bold cyan]Starting Trading Bot - Mode: {settings.trading_mode.value.upper()}[/bold cyan]"
    )
    console.print(f"[dim]Interval: {interval}s | Symbols: {', '.join(symbol_list)}[/dim]\n")

    cycle = 0
    while True:
        cycle += 1
        console.rule(f"Cycle #{cycle}")

        try:
            # Fetch data
            market_data_list = fetcher.fetch_multiple(symbol_list)
            if not market_data_list:
                console.print("[red]No data fetched, retrying next cycle.[/red]")
                time.sleep(interval)
                continue

            display_market_data(market_data_list)

            # Analyze
            console.print("[bold]Analyzing with ChatGPT...[/bold]\n")
            report = analyst.analyze(market_data_list)
            display_analysis_report(report)

            # Execute
            console.print("[bold]Executing recommendations...[/bold]\n")
            orders = executor.execute_recommendations(report)
            display_executed_orders(orders)

            # Portfolio
            prices = {d.symbol: d.current_price for d in market_data_list}
            paper_trader.update_prices(prices)
            display_portfolio(paper_trader.get_portfolio())

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Bot stopped by user.[/bold yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error in cycle #{cycle}: {e}[/red]")

        console.print(f"[dim]Next cycle in {interval} seconds...[/dim]\n")
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Bot stopped by user.[/bold yellow]")
            break


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
