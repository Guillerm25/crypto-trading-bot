"""Tests for the free-text analysis parser."""

from trading_bot.models import SignalStrength
from trading_bot.text_parser import parse_analysis_text


def test_parse_buy_signal_spanish():
    text = (
        "Recomiendo comprar BTC con entrada en $80,000, "
        "stop-loss en $78,000 y take-profit en $85,000. Confianza: 75%."
    )
    report = parse_analysis_text(text)
    assert len(report.recommendations) == 1
    rec = report.recommendations[0]
    assert rec.symbol == "BTC/USDT"
    assert rec.signal == SignalStrength.BUY
    assert rec.confidence == 0.75
    assert rec.entry_price == 80000.0
    assert rec.stop_loss == 78000.0
    assert rec.take_profit == 85000.0


def test_parse_sell_signal_english():
    text = "I recommend to sell ETH at the current price. Target: $2,000."
    report = parse_analysis_text(text)
    assert len(report.recommendations) == 1
    rec = report.recommendations[0]
    assert rec.symbol == "ETH/USDT"
    assert rec.signal == SignalStrength.SELL


def test_parse_hold_signal():
    text = "Mantener SOL en la posición actual. El mercado está indeciso."
    report = parse_analysis_text(text)
    assert len(report.recommendations) == 1
    rec = report.recommendations[0]
    assert rec.symbol == "SOL/USDT"
    assert rec.signal == SignalStrength.HOLD


def test_parse_multiple_symbols():
    text = """
    BTC: comprar a $80,000 con stop-loss $78,000. Confianza: 80%.
    ETH: vender con objetivo $2,500.
    SOL: hold, esperar mejor momento.
    """
    report = parse_analysis_text(text)
    assert len(report.recommendations) == 3
    symbols = {r.symbol for r in report.recommendations}
    assert symbols == {"BTC/USDT", "ETH/USDT", "SOL/USDT"}


def test_parse_strong_buy():
    text = "Strong buy on BTC. Entry $80,000."
    report = parse_analysis_text(text)
    assert len(report.recommendations) == 1
    assert report.recommendations[0].signal == SignalStrength.STRONG_BUY


def test_parse_no_symbols():
    text = "The market is looking uncertain today. I would wait."
    report = parse_analysis_text(text)
    assert len(report.recommendations) == 0


def test_parse_default_confidence():
    text = "Buy BTC at $80,000."
    report = parse_analysis_text(text)
    assert len(report.recommendations) == 1
    assert report.recommendations[0].confidence == 0.7


def test_parse_crypto_full_names():
    text = "Comprar Bitcoin y vender Ethereum."
    report = parse_analysis_text(text)
    assert len(report.recommendations) == 2
    symbols = {r.symbol for r in report.recommendations}
    assert symbols == {"BTC/USDT", "ETH/USDT"}


def test_parse_empty_text():
    report = parse_analysis_text("")
    assert len(report.recommendations) == 0


def test_report_has_raw_analysis():
    text = "Buy BTC at $80,000. Sell ETH."
    report = parse_analysis_text(text)
    assert report.raw_analysis == text
    assert report.market_summary != ""
