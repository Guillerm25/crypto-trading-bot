"""Rich-based CLI dashboard for displaying reports and portfolio status."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from trading_bot.models import (
    AnalysisReport,
    MarketData,
    Order,
    OrderStatus,
    Portfolio,
    SignalStrength,
)

console = Console()

SIGNAL_COLORS = {
    SignalStrength.STRONG_BUY: "bold green",
    SignalStrength.BUY: "green",
    SignalStrength.HOLD: "yellow",
    SignalStrength.SELL: "red",
    SignalStrength.STRONG_SELL: "bold red",
}

SIGNAL_LABELS = {
    SignalStrength.STRONG_BUY: "STRONG BUY",
    SignalStrength.BUY: "BUY",
    SignalStrength.HOLD: "HOLD",
    SignalStrength.SELL: "SELL",
    SignalStrength.STRONG_SELL: "STRONG SELL",
}


def display_market_data(market_data_list: list[MarketData]) -> None:
    """Display market data in a formatted table."""
    table = Table(title="Market Data", show_header=True, header_style="bold cyan")
    table.add_column("Symbol", style="bold")
    table.add_column("Price", justify="right")
    table.add_column("24h Change", justify="right")
    table.add_column("24h Volume", justify="right")
    table.add_column("24h High", justify="right")
    table.add_column("24h Low", justify="right")

    for data in market_data_list:
        change_color = "green" if data.change_24h >= 0 else "red"
        table.add_row(
            data.symbol,
            f"${data.current_price:,.2f}",
            f"[{change_color}]{data.change_24h:+.2f}%[/{change_color}]",
            f"${data.volume_24h:,.0f}",
            f"${data.high_24h:,.2f}",
            f"${data.low_24h:,.2f}",
        )

    console.print(table)
    console.print()


def display_analysis_report(report: AnalysisReport) -> None:
    """Display the AI analysis report."""
    console.print(Panel(report.market_summary, title="Market Summary", border_style="blue"))
    console.print()

    table = Table(title="Trading Recommendations", show_header=True, header_style="bold magenta")
    table.add_column("Symbol", style="bold")
    table.add_column("Signal", justify="center")
    table.add_column("Confidence", justify="center")
    table.add_column("Entry", justify="right")
    table.add_column("Stop Loss", justify="right")
    table.add_column("Take Profit", justify="right")
    table.add_column("Size %", justify="right")

    for rec in report.recommendations:
        color = SIGNAL_COLORS.get(rec.signal, "white")
        label = SIGNAL_LABELS.get(rec.signal, rec.signal.value)

        table.add_row(
            rec.symbol,
            f"[{color}]{label}[/{color}]",
            f"{rec.confidence:.0%}",
            f"${rec.entry_price:,.2f}" if rec.entry_price else "-",
            f"${rec.stop_loss:,.2f}" if rec.stop_loss else "-",
            f"${rec.take_profit:,.2f}" if rec.take_profit else "-",
            f"{rec.position_size_pct:.1%}",
        )

    console.print(table)
    console.print()

    if report.recommendations:
        for rec in report.recommendations:
            if rec.reasoning:
                console.print(f"  [bold]{rec.symbol}[/bold]: {rec.reasoning}")
        console.print()

    console.print(Panel(report.risk_assessment, title="Risk Assessment", border_style="yellow"))
    console.print()


def display_portfolio(portfolio: Portfolio) -> None:
    """Display portfolio status."""
    total_value = portfolio.total_value
    return_pct = portfolio.return_pct
    return_color = "green" if return_pct >= 0 else "red"

    table = Table(title="Portfolio Summary", show_header=False, border_style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Cash Balance", f"${portfolio.balance:,.2f}")
    table.add_row("Total Value", f"${total_value:,.2f}")
    table.add_row("Return", f"[{return_color}]{return_pct:+.2f}%[/{return_color}]")
    table.add_row("Total PnL", f"[{return_color}]${portfolio.total_pnl:+,.2f}[/{return_color}]")
    table.add_row("Total Trades", str(portfolio.total_trades))
    table.add_row("Win Rate", f"{portfolio.win_rate:.0%}")

    console.print(table)
    console.print()

    if portfolio.positions:
        pos_table = Table(title="Open Positions", show_header=True, header_style="bold green")
        pos_table.add_column("Symbol", style="bold")
        pos_table.add_column("Amount", justify="right")
        pos_table.add_column("Entry Price", justify="right")
        pos_table.add_column("Current Price", justify="right")
        pos_table.add_column("Unrealized PnL", justify="right")

        for symbol, pos in portfolio.positions.items():
            pnl_color = "green" if pos.unrealized_pnl >= 0 else "red"
            pos_table.add_row(
                symbol,
                f"{pos.amount:.6f}",
                f"${pos.entry_price:,.2f}",
                f"${pos.current_price:,.2f}",
                f"[{pnl_color}]${pos.unrealized_pnl:+,.2f}[/{pnl_color}]",
            )

        console.print(pos_table)
        console.print()


def display_executed_orders(orders: list[Order]) -> None:
    """Display executed orders."""
    if not orders:
        console.print("[dim]No orders executed.[/dim]")
        return

    table = Table(title="Executed Orders", show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("Symbol")
    table.add_column("Side")
    table.add_column("Amount", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Status")

    for order in orders:
        side_color = "green" if order.side.value == "buy" else "red"
        status_color = "green" if order.status == OrderStatus.FILLED else "red"
        table.add_row(
            order.id,
            order.symbol,
            f"[{side_color}]{order.side.value.upper()}[/{side_color}]",
            f"{order.amount:.6f}",
            f"${order.filled_price:,.2f}" if order.filled_price else "-",
            f"[{status_color}]{order.status.value}[/{status_color}]",
        )

    console.print(table)
    console.print()
