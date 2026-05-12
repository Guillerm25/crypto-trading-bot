"""Parse free-text analysis into trade recommendations."""

import re

from trading_bot.models import AnalysisReport, SignalStrength, TradeRecommendation

KNOWN_SYMBOLS = {
    "BTC": "BTC/USDT",
    "BITCOIN": "BTC/USDT",
    "ETH": "ETH/USDT",
    "ETHEREUM": "ETH/USDT",
    "SOL": "SOL/USDT",
    "SOLANA": "SOL/USDT",
    "XRP": "XRP/USDT",
    "RIPPLE": "XRP/USDT",
    "ADA": "ADA/USDT",
    "CARDANO": "ADA/USDT",
    "DOGE": "DOGE/USDT",
    "DOGECOIN": "DOGE/USDT",
    "DOT": "DOT/USDT",
    "POLKADOT": "DOT/USDT",
    "AVAX": "AVAX/USDT",
    "AVALANCHE": "AVAX/USDT",
    "LINK": "LINK/USDT",
    "CHAINLINK": "LINK/USDT",
    "MATIC": "MATIC/USDT",
    "POLYGON": "MATIC/USDT",
    "UNI": "UNI/USDT",
    "UNISWAP": "UNI/USDT",
    "ATOM": "ATOM/USDT",
    "COSMOS": "ATOM/USDT",
    "LTC": "LTC/USDT",
    "LITECOIN": "LTC/USDT",
    "SHIB": "SHIB/USDT",
    "BNB": "BNB/USDT",
    "NEAR": "NEAR/USDT",
    "APT": "APT/USDT",
    "APTOS": "APT/USDT",
    "ARB": "ARB/USDT",
    "ARBITRUM": "ARB/USDT",
    "OP": "OP/USDT",
    "OPTIMISM": "OP/USDT",
    "SUI": "SUI/USDT",
    "PEPE": "PEPE/USDT",
}

BUY_KEYWORDS = [
    "comprar", "compra", "buy", "long", "alcista", "bullish",
    "strong buy", "strong_buy", "compra fuerte",
]
SELL_KEYWORDS = [
    "vender", "venta", "sell", "short", "bajista", "bearish",
    "strong sell", "strong_sell", "venta fuerte",
]
HOLD_KEYWORDS = ["hold", "mantener", "neutral", "esperar", "wait"]

_PRICE_PATTERN = re.compile(
    r"\$?\s*([\d,]+\.?\d*)", re.IGNORECASE
)


def _extract_price(text: str, keywords: list[str]) -> float | None:
    """Extract a price near one of the given keywords."""
    text_lower = text.lower()
    for kw in keywords:
        idx = text_lower.find(kw)
        if idx == -1:
            continue
        window = text[idx : idx + 80]
        match = _PRICE_PATTERN.search(window)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def _detect_signal(block: str) -> SignalStrength:
    """Detect the trade signal from a text block."""
    lower = block.lower()
    strong_buy = any(k in lower for k in ["strong buy", "strong_buy", "compra fuerte"])
    strong_sell = any(k in lower for k in ["strong sell", "strong_sell", "venta fuerte"])
    if strong_buy:
        return SignalStrength.STRONG_BUY
    if strong_sell:
        return SignalStrength.STRONG_SELL
    has_buy = any(k in lower for k in BUY_KEYWORDS)
    has_sell = any(k in lower for k in SELL_KEYWORDS)
    has_hold = any(k in lower for k in HOLD_KEYWORDS)
    if has_buy and not has_sell:
        return SignalStrength.BUY
    if has_sell and not has_buy:
        return SignalStrength.SELL
    if has_hold:
        return SignalStrength.HOLD
    return SignalStrength.HOLD


def _extract_confidence(block: str) -> float:
    """Extract confidence from text, default 0.7 if not found."""
    patterns = [
        r"confian[zc]a[:\s]+(\d+)\s*%",
        r"confidence[:\s]+(\d+)\s*%",
        r"(\d+)\s*%\s*(?:confidence|confianza)",
        r"probabilidad[:\s]+(\d+)\s*%",
    ]
    for pattern in patterns:
        match = re.search(pattern, block, re.IGNORECASE)
        if match:
            return min(float(match.group(1)) / 100.0, 1.0)
    return 0.7


def parse_analysis_text(text: str, quote_currency: str = "USDT") -> AnalysisReport:
    """Parse free-text analysis into an AnalysisReport.

    Supports text in Spanish or English. Detects symbols like BTC, ETH, SOL
    and maps them to trading pairs. Extracts buy/sell/hold signals,
    entry prices, stop-loss, and take-profit levels from natural language.
    """
    recommendations: list[TradeRecommendation] = []
    symbol_tokens: dict[str, list[str]] = {}

    for token, symbol in KNOWN_SYMBOLS.items():
        pattern = rf"\b{re.escape(token)}\b"
        if re.search(pattern, text, re.IGNORECASE):
            symbol_tokens.setdefault(symbol, []).append(token)

    all_tokens_pattern = "|".join(
        re.escape(t) for t in sorted(KNOWN_SYMBOLS, key=len, reverse=True)
    )
    all_mentions = list(
        re.finditer(rf"(?i)\b(?:{all_tokens_pattern})\b", text)
    )
    mention_starts = sorted({m.start() for m in all_mentions})

    for symbol in sorted(symbol_tokens):
        tokens = symbol_tokens[symbol]
        alt = "|".join(re.escape(t) for t in tokens)
        pattern = rf"(?i)\b(?:{alt})\b"
        matches = list(re.finditer(pattern, text))
        if not matches:
            continue

        first_pos = matches[0].start()
        idx = mention_starts.index(first_pos) if first_pos in mention_starts else -1

        lookback = text[max(0, first_pos - 80) : first_pos]
        newline_pos = lookback.rfind("\n")
        if newline_pos >= 0:
            block_start = max(0, first_pos - 80) + newline_pos + 1
        else:
            block_start = max(0, first_pos - 80)
        if idx >= 0 and idx + 1 < len(mention_starts):
            block_end = mention_starts[idx + 1]
        else:
            block_end = min(len(text), matches[0].end() + 300)

        block = text[block_start:block_end]
        if idx >= 0 and idx + 1 < len(mention_starts):
            sym_offset = first_pos - block_start
            para_break = block.find("\n\n", sym_offset)
            if para_break > 0:
                block = block[:para_break]

        signal = _detect_signal(block)
        confidence = _extract_confidence(block)

        entry_price = _extract_price(
            block,
            ["entry", "entrada", "precio", "price", "comprar", "buy", "a "],
        )
        stop_loss = _extract_price(
            block,
            ["stop-loss", "stop loss", "stoploss", "sl", "stop"],
        )
        take_profit = _extract_price(
            block,
            [
                "take-profit", "take profit", "takeprofit",
                "tp", "objetivo", "target",
            ],
        )

        recommendations.append(
            TradeRecommendation(
                symbol=symbol,
                signal=signal,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size_pct=0.05,
                reasoning=block.strip()[:200],
            )
        )

    return AnalysisReport(
        market_summary="Analysis parsed from user-provided text.",
        recommendations=recommendations,
        risk_assessment="Manual analysis — verify signals before executing.",
        raw_analysis=text,
    )
