"""
Composite Signals Module for TradingAgents

Pre-computes derived trading signals from raw OHLCV data, reducing the LLM's
burden of mentally correlating individual indicator values. All calculations
use data available for free from Yahoo Finance via yfinance.
"""

import os
from datetime import datetime
from typing import Annotated

import pandas as pd
import yfinance as yf
from stockstats import wrap

from .config import get_config


def get_composite_signals(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "The current trading date, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 60,
) -> str:
    """
    Compute composite / derived trading signals from raw OHLCV data.

    Returns a structured text report covering:
    - Golden/Death Cross status
    - Bollinger Band Width & squeeze detection
    - Volume surge detection
    - RSI-MACD divergence detection
    - Multi-timeframe trend alignment

    All data is sourced from Yahoo Finance (free).
    """
    try:
        config = get_config()

        curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")

        # Fetch data — we need extra history for 200 SMA
        # We look back 2 years from curr_date to ensure we have enough data for a 200 SMA
        start_date = curr_date_dt - pd.DateOffset(years=2)
        end_date = curr_date_dt + pd.DateOffset(days=1)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        os.makedirs(config["data_cache_dir"], exist_ok=True)
        data_file = os.path.join(
            config["data_cache_dir"],
            f"{symbol}-YFin-data-{start_date_str}-{end_date_str}.csv",
        )

        if os.path.exists(data_file):
            data = pd.read_csv(data_file)
            data["Date"] = pd.to_datetime(data["Date"])
        else:
            data = yf.download(
                symbol,
                start=start_date_str,
                end=end_date_str,
                multi_level_index=False,
                progress=False,
                auto_adjust=True,
            )
            data = data.reset_index()
            data.to_csv(data_file, index=False)

        if data.empty:
            return f"No data available for {symbol} to compute composite signals."

        df = wrap(data.copy())

        # Filter to data up to curr_date
        df["Date"] = pd.to_datetime(df["Date"])
        df = df[df["Date"] <= curr_date_dt].copy()

        if len(df) < 50:
            return f"Insufficient data for {symbol} to compute composite signals (need at least 50 trading days)."

        latest = df.iloc[-1]
        latest_date = latest["Date"].strftime("%Y-%m-%d")
        sections = []

        # ── 1. Golden / Death Cross ──────────────────────────────────────
        try:
            df["close_50_sma"]  # trigger calculation
            df["close_200_sma"]

            sma50 = df["close_50_sma"].iloc[-1]
            sma200 = df["close_200_sma"].iloc[-1]

            if pd.notna(sma50) and pd.notna(sma200):
                cross_status = "GOLDEN CROSS (Bullish)" if sma50 > sma200 else "DEATH CROSS (Bearish)"
                spread_pct = ((sma50 - sma200) / sma200) * 100

                # Check for recent crossover (within last 10 days)
                recent_crossover = "No"
                if len(df) >= 11:
                    for i in range(-10, -1):
                        prev_50 = df["close_50_sma"].iloc[i]
                        prev_200 = df["close_200_sma"].iloc[i]
                        curr_50 = df["close_50_sma"].iloc[i + 1]
                        curr_200 = df["close_200_sma"].iloc[i + 1]
                        if pd.notna(prev_50) and pd.notna(prev_200) and pd.notna(curr_50) and pd.notna(curr_200):
                            if (prev_50 <= prev_200 and curr_50 > curr_200):
                                recent_crossover = f"YES — Golden Cross on {df['Date'].iloc[i + 1].strftime('%Y-%m-%d')}"
                            elif (prev_50 >= prev_200 and curr_50 < curr_200):
                                recent_crossover = f"YES — Death Cross on {df['Date'].iloc[i + 1].strftime('%Y-%m-%d')}"

                sections.append(
                    f"## 1. Moving Average Cross Status\n"
                    f"- Status: **{cross_status}**\n"
                    f"- 50 SMA: {sma50:.2f} | 200 SMA: {sma200:.2f}\n"
                    f"- Spread: {spread_pct:+.2f}%\n"
                    f"- Recent Crossover (last 10 days): {recent_crossover}\n"
                )
            else:
                sections.append("## 1. Moving Average Cross Status\n- Insufficient data for 200 SMA calculation.\n")
        except Exception as e:
            sections.append(f"## 1. Moving Average Cross Status\n- Error: {e}\n")

        # ── 2. Bollinger Band Width & Squeeze ────────────────────────────
        try:
            df["boll_ub"]
            df["boll_lb"]
            df["boll"]

            bb_upper = df["boll_ub"].iloc[-1]
            bb_lower = df["boll_lb"].iloc[-1]
            bb_mid = df["boll"].iloc[-1]
            close_price = df["close"].iloc[-1]

            if pd.notna(bb_upper) and pd.notna(bb_lower) and pd.notna(bb_mid) and bb_mid > 0:
                bb_width = ((bb_upper - bb_lower) / bb_mid) * 100

                # Historical BB width for comparison
                df["_bb_width"] = ((df["boll_ub"] - df["boll_lb"]) / df["boll"]) * 100
                bb_width_20_avg = df["_bb_width"].tail(20).mean()
                bb_width_percentile = (df["_bb_width"] <= bb_width).sum() / len(df) * 100

                squeeze = "YES — Volatility squeeze detected!" if bb_width_percentile < 20 else "No"
                price_position = "Above upper band (overbought)" if close_price > bb_upper else \
                                "Below lower band (oversold)" if close_price < bb_lower else \
                                "Within bands"

                sections.append(
                    f"## 2. Bollinger Band Width & Squeeze Detection\n"
                    f"- Current BB Width: {bb_width:.2f}%\n"
                    f"- 20-day Avg BB Width: {bb_width_20_avg:.2f}%\n"
                    f"- BB Width Percentile: {bb_width_percentile:.0f}th (lower = tighter)\n"
                    f"- Squeeze Detected: **{squeeze}**\n"
                    f"- Price Position: {price_position} (Close: {close_price:.2f})\n"
                )
            else:
                sections.append("## 2. Bollinger Band Width & Squeeze Detection\n- Insufficient data.\n")
        except Exception as e:
            sections.append(f"## 2. Bollinger Band Width & Squeeze Detection\n- Error: {e}\n")

        # ── 3. Volume Surge Detection ────────────────────────────────────
        try:
            vol_col = next(
                (c for c in df.columns if c.lower() == "volume"), None
            )
            if vol_col is not None:
                current_vol = df[vol_col].iloc[-1]
                avg_vol_20 = df[vol_col].tail(20).mean()

                if avg_vol_20 > 0:
                    vol_ratio = current_vol / avg_vol_20

                    surge_status = "MAJOR SURGE (>2x)" if vol_ratio > 2.0 else \
                                  "Elevated (>1.5x)" if vol_ratio > 1.5 else \
                                  "Normal" if vol_ratio > 0.7 else \
                                  "Below average (<0.7x)"

                    # Check last 5 days for volume trend
                    recent_vols = df[vol_col].tail(5).tolist()
                    vol_trend = "Rising" if all(recent_vols[i] <= recent_vols[i+1] for i in range(len(recent_vols)-1)) else \
                               "Falling" if all(recent_vols[i] >= recent_vols[i+1] for i in range(len(recent_vols)-1)) else \
                               "Mixed"

                    sections.append(
                        f"## 3. Volume Surge Detection\n"
                        f"- Current Volume: {current_vol:,.0f}\n"
                        f"- 20-day Avg Volume: {avg_vol_20:,.0f}\n"
                        f"- Volume Ratio: {vol_ratio:.2f}x\n"
                        f"- Status: **{surge_status}**\n"
                        f"- 5-day Volume Trend: {vol_trend}\n"
                    )
                else:
                    sections.append("## 3. Volume Surge Detection\n- No volume data available.\n")
            else:
                sections.append("## 3. Volume Surge Detection\n- Volume column not found.\n")
        except Exception as e:
            sections.append(f"## 3. Volume Surge Detection\n- Error: {e}\n")

        # ── 4. RSI-Price Divergence Detection ────────────────────────────
        try:
            df["rsi_14"]  # trigger RSI calculation

            if len(df) >= 20:
                recent_prices = df["close"].tail(20)
                recent_rsi = df["rsi_14"].tail(20)

                # Simple divergence: price making new highs but RSI not, or vice versa
                price_10d_change = (df["close"].iloc[-1] - df["close"].iloc[-10]) / df["close"].iloc[-10] * 100
                rsi_10d_change = df["rsi_14"].iloc[-1] - df["rsi_14"].iloc[-10]

                divergence = "None detected"
                if price_10d_change > 2 and rsi_10d_change < -5:
                    divergence = "BEARISH DIVERGENCE — Price rising but RSI falling (weakening momentum)"
                elif price_10d_change < -2 and rsi_10d_change > 5:
                    divergence = "BULLISH DIVERGENCE — Price falling but RSI rising (building momentum)"

                curr_rsi = df["rsi_14"].iloc[-1]
                rsi_status = "Overbought (>70)" if curr_rsi > 70 else \
                            "Oversold (<30)" if curr_rsi < 30 else \
                            "Neutral"

                sections.append(
                    f"## 4. RSI-Price Divergence\n"
                    f"- Current RSI: {curr_rsi:.1f} ({rsi_status})\n"
                    f"- 10-day Price Change: {price_10d_change:+.2f}%\n"
                    f"- 10-day RSI Change: {rsi_10d_change:+.1f} points\n"
                    f"- Divergence: **{divergence}**\n"
                )
            else:
                sections.append("## 4. RSI-Price Divergence\n- Insufficient data.\n")
        except Exception as e:
            sections.append(f"## 4. RSI-Price Divergence\n- Error: {e}\n")

        # ── 5. Multi-Timeframe Trend Summary ─────────────────────────────
        try:
            close = df["close"].iloc[-1]
            trends = {}

            for label, col in [("10 EMA", "close_10_ema"), ("20 SMA", "close_20_sma"),
                                ("50 SMA", "close_50_sma"), ("200 SMA", "close_200_sma")]:
                try:
                    df[col]
                    val = df[col].iloc[-1]
                    if pd.notna(val):
                        trends[label] = "Bullish ↑" if close > val else "Bearish ↓"
                except Exception:
                    pass

            if trends:
                bullish_count = sum(1 for v in trends.values() if "Bullish" in v)
                total = len(trends)
                alignment = "STRONG BULLISH" if bullish_count == total else \
                           "MOSTLY BULLISH" if bullish_count >= total * 0.75 else \
                           "MIXED" if bullish_count >= total * 0.25 else \
                           "MOSTLY BEARISH" if bullish_count > 0 else \
                           "STRONG BEARISH"

                trend_lines = "\n".join(f"  - {k}: {v}" for k, v in trends.items())
                sections.append(
                    f"## 5. Multi-Timeframe Trend Alignment\n"
                    f"- Close: {close:.2f}\n"
                    f"- Overall: **{alignment}** ({bullish_count}/{total} bullish)\n"
                    f"{trend_lines}\n"
                )
        except Exception as e:
            sections.append(f"## 5. Multi-Timeframe Trend Alignment\n- Error: {e}\n")

        # ── Assemble report ──────────────────────────────────────────────
        header = (
            f"# Composite Trading Signals for {symbol.upper()}\n"
            f"Analysis date: {latest_date} | Lookback: {look_back_days} days\n\n"
        )

        return header + "\n".join(sections)

    except Exception as e:
        return f"Error computing composite signals for {symbol}: {str(e)}"
