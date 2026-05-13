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

    if settings.trading_mode == TradingMode.SANDBOX:
        if not settings.bybit_testnet_api_key:
            console.print(
                "[red]Error: Sandbox mode requires BYBIT_TESTNET_API_KEY "
                "and BYBIT_TESTNET_API_SECRET.[/red]"
            )
            raise SystemExit(1)
        sandbox_trader = SandboxTrader(settings)
        mode_label = "Demo Trading" if settings.bybit_demo_trading else "Testnet"
        console.print(
            f"[bold magenta]Mode: SANDBOX (Bybit {mode_label})[/bold magenta]\n"
        )
        ok, msg = sandbox_trader.validate_credentials()
        if not ok:
            console.print(
                f"[red]Error: {msg}\n\n"
                "Check your .env config:\n"
                "- If you created keys from Demo Trading on bybit.eu, "
                "set BYBIT_DEMO_TRADING=true\n"
                "- If you created keys from testnet.bybit.com, "
                "set BYBIT_DEMO_TRADING=false\n"
                "- Make sure BYBIT_HOSTNAME matches your region "
                "(bybit.eu for Europe)[/red]"
            )
            raise SystemExit(1)
        console.print(f"[bold]Bybit {mode_label} Balances:[/bold]")
        try:
            balances = sandbox_trader.fetch_balance()
            if balances:
                for currency, amount in sorted(balances.items()):
                    console.print(f"  {currency}: {amount:,.8f}")
            else:
                console.print("  [yellow]No funds in account.[/yellow]")
        except Exception as exc:
            console.print(f"  [yellow]Could not fetch balances: {exc}[/yellow]")
        console.print()

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
                    "and BYBIT_TESTNET_API_SECRET.[/red]"
                )
                raise SystemExit(1)
            sandbox_trader = SandboxTrader(settings)
            mode_label = (
                "Demo Trading" if settings.bybit_demo_trading else "Testnet"
            )
            console.print(
                f"[bold magenta]Mode: SANDBOX — orders sent to Bybit "
                f"{mode_label}[/bold magenta]"
            )
            ok, msg = sandbox_trader.validate_credentials()
            if not ok:
                console.print(
                    f"[red]Error: {msg}\n\n"
                    "Check your .env config:\n"
                    "- If you created keys from Demo Trading on bybit.eu, "
                    "set BYBIT_DEMO_TRADING=true\n"
                    "- If you created keys from testnet.bybit.com, "
                    "set BYBIT_DEMO_TRADING=false[/red]"
                )
                raise SystemExit(1)
            console.print(
                "[green]Credentials validated successfully.[/green]\n"
            )

        executor = TradeExecutor(settings, fetcher, paper_trader, sandbox_trader)

        console.print("[bold]Executing recommendations...[/bold]\n")
        orders = executor.execute_recommendations(report)
        display_executed_orders(orders)

        if settings.trading_mode == TradingMode.SANDBOX and sandbox_trader:
            mode_label = (
                "Demo Trading" if settings.bybit_demo_trading else "Testnet"
            )
            console.print(f"\n[bold]Bybit {mode_label} Balances:[/bold]")
            try:
                balances = sandbox_trader.fetch_balance()
                if balances:
                    for currency, amount in sorted(balances.items()):
                        console.print(f"  {currency}: {amount:,.8f}")
                else:
                    console.print("  [yellow]No funds in account.[/yellow]")
            except Exception as exc:
                console.print(f"  [yellow]Could not fetch balances: {exc}[/yellow]")

        console.print("\n[bold]Portfolio Status:[/bold]")
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


@cli.command()
def diagnose() -> None:
    """Show available symbols and connection info for debugging."""
    settings = load_settings()
    console.print(f"[bold]Trading Mode:[/bold] {settings.trading_mode.value}")
    console.print(f"[bold]Bybit Hostname:[/bold] {settings.bybit_hostname}")
    console.print(
        f"[bold]Demo Trading:[/bold] {settings.bybit_demo_trading}\n"
    )

    console.print("[bold]Mainnet markets (bybit.com):[/bold]")
    fetcher = MarketDataFetcher(settings)
    usdt_symbols = [
        s for s in sorted(fetcher.exchange.symbols) if "/USDT" in s
    ]
    spot = [s for s in usdt_symbols if ":" not in s]
    linear = [s for s in usdt_symbols if ":USDT" in s]
    console.print(f"  Spot USDT pairs: {len(spot)}")
    console.print(f"  Linear USDT pairs: {len(linear)}")
    for sym in settings.trading_symbols:
        resolved = fetcher._resolve_symbol(sym)
        status = "spot" if ":" not in resolved else "linear"
        console.print(f"  {sym} -> {resolved} ({status})")

    if settings.trading_mode == TradingMode.SANDBOX:
        console.print(f"\n[bold]Testnet markets ({settings.bybit_hostname}):[/bold]")
        if not settings.bybit_testnet_api_key:
            console.print("  [red]No testnet credentials configured[/red]")
        else:
            try:
                sandbox = SandboxTrader(settings)
                t_usdt = [
                    s
                    for s in sorted(sandbox.exchange.symbols)
                    if "/USDT" in s
                ]
                t_spot = [s for s in t_usdt if ":" not in s]
                t_linear = [s for s in t_usdt if ":USDT" in s]
                console.print(f"  Spot USDT pairs: {len(t_spot)}")
                console.print(f"  Linear USDT pairs: {len(t_linear)}")
                if t_spot:
                    console.print(f"  Spot examples: {', '.join(t_spot[:10])}")
                if t_linear:
                    console.print(
                        f"  Linear examples: {', '.join(t_linear[:10])}"
                    )
                for sym in settings.trading_symbols:
                    try:
                        resolved = sandbox._resolve_symbol(sym)
                        status = "spot" if ":" not in resolved else "linear"
                        console.print(f"  {sym} -> {resolved} ({status})")
                    except Exception:
                        console.print(f"  {sym} -> [red]NOT AVAILABLE[/red]")
            except Exception as exc:
                console.print(f"  [red]Error: {exc}[/red]")


if __name__ == "__main__":
    cli()
