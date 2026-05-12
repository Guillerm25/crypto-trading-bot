"""AI-powered market analysis using ChatGPT (OpenAI)."""

import json
from datetime import UTC, datetime

import openai

from trading_bot.config import Settings
from trading_bot.models import AnalysisReport, MarketData, SignalStrength, TradeRecommendation

ANALYSIS_SYSTEM_PROMPT = """You are an expert cryptocurrency trading analyst.
You analyze market data and provide actionable trading recommendations.

Your analysis should include:
1. A concise market summary for each asset
2. Specific trade recommendations with entry, stop-loss, and take-profit levels
3. Position sizing as a percentage of portfolio (0.01 to 0.10)
4. Confidence level (0.0 to 1.0) for each recommendation
5. Risk assessment for the overall market

IMPORTANT: You MUST respond with valid JSON only. No markdown, no code blocks, no extra text.

Response format (JSON):
{
    "market_summary": "Brief overview of current market conditions",
    "recommendations": [
        {
            "symbol": "BTC/USDT",
            "signal": "buy|sell|hold|strong_buy|strong_sell",
            "confidence": 0.75,
            "entry_price": 50000.0,
            "stop_loss": 48000.0,
            "take_profit": 55000.0,
            "position_size_pct": 0.05,
            "reasoning": "Why this trade makes sense"
        }
    ],
    "risk_assessment": "Overall risk evaluation and warnings"
}

Be conservative with confidence levels. Only recommend trades with clear technical
or fundamental reasoning. Always include stop-loss levels to manage risk."""


def _format_market_data(market_data_list: list[MarketData]) -> str:
    """Format market data into a readable string for the AI."""
    lines: list[str] = []
    for data in market_data_list:
        lines.append(f"\n=== {data.symbol} ===")
        lines.append(f"Current Price: ${data.current_price:,.2f}")
        lines.append(f"24h Change: {data.change_24h:+.2f}%")
        lines.append(f"24h Volume: ${data.volume_24h:,.0f}")
        lines.append(f"24h High: ${data.high_24h:,.2f}")
        lines.append(f"24h Low: ${data.low_24h:,.2f}")

        if data.candles:
            lines.append(f"\nRecent candles (last {len(data.candles)} periods):")
            for candle in data.candles[-12:]:
                change = ((candle.close - candle.open) / candle.open) * 100 if candle.open else 0
                lines.append(
                    f"  {candle.timestamp.strftime('%Y-%m-%d %H:%M')} | "
                    f"O:{candle.open:,.2f} H:{candle.high:,.2f} "
                    f"L:{candle.low:,.2f} C:{candle.close:,.2f} "
                    f"V:{candle.volume:,.0f} ({change:+.2f}%)"
                )

    return "\n".join(lines)


def _parse_recommendations(raw: dict) -> list[TradeRecommendation]:
    """Parse recommendations from the AI response."""
    recommendations: list[TradeRecommendation] = []
    for rec in raw.get("recommendations", []):
        signal_str = rec.get("signal", "hold").lower()
        signal_map = {
            "strong_buy": SignalStrength.STRONG_BUY,
            "buy": SignalStrength.BUY,
            "hold": SignalStrength.HOLD,
            "sell": SignalStrength.SELL,
            "strong_sell": SignalStrength.STRONG_SELL,
        }
        signal = signal_map.get(signal_str, SignalStrength.HOLD)

        recommendations.append(
            TradeRecommendation(
                symbol=rec.get("symbol", ""),
                signal=signal,
                confidence=float(rec.get("confidence", 0.5)),
                entry_price=rec.get("entry_price"),
                stop_loss=rec.get("stop_loss"),
                take_profit=rec.get("take_profit"),
                position_size_pct=float(rec.get("position_size_pct", 0.05)),
                reasoning=rec.get("reasoning", ""),
            )
        )
    return recommendations


class AIAnalyst:
    """AI-powered market analyst using ChatGPT."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = openai.OpenAI(api_key=settings.openai_api_key)

    def analyze(self, market_data_list: list[MarketData]) -> AnalysisReport:
        """Analyze market data and generate trading recommendations."""
        formatted_data = _format_market_data(market_data_list)

        user_prompt = (
            f"Analyze the following cryptocurrency market data and provide "
            f"trading recommendations:\n\n{formatted_data}\n\n"
            f"Current time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Respond with JSON only."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.settings.analysis_model,
                max_tokens=self.settings.max_tokens,
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except openai.AuthenticationError:
            raise SystemExit(
                "Error: Invalid OPENAI_API_KEY. Check your .env file or environment variable."
            )

        raw_text = response.choices[0].message.content or ""

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            raise SystemExit(f"Error: Could not parse AI response as JSON:\n{raw_text[:500]}")

        return AnalysisReport(
            market_summary=parsed.get("market_summary", ""),
            recommendations=_parse_recommendations(parsed),
            risk_assessment=parsed.get("risk_assessment", ""),
            raw_analysis=raw_text,
        )
