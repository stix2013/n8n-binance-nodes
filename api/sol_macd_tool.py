#!/usr/bin/env python3
"""
SOL MACD Analysis Tool
Simple script to get MACD analysis for Solana (SOL)
"""

import requests
import json


def get_sol_analysis(symbol="SOLUSDT", interval="1h", limit=100):
    """Get MACD analysis for SOL"""

    base_url = "http://localhost:8000/api"

    # Full analysis endpoint
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    try:
        response = requests.get(f"{base_url}/analysis", params=params)

        if response.status_code == 200:
            data = response.json()

            print(f"📊 {symbol} MACD Analysis")
            print("=" * 30)
            print(f"💰 Current Price: ${data['current_price']:,.2f}")
            print()

            # RSI
            rsi = data["rsi"]
            print(f"📈 RSI: {rsi['value']:.2f} ({rsi['signal']})")

            # MACD
            macd = data["macd"]
            print(f"📊 MACD Line: {macd['macd_line']:.4f}")
            print(f"📊 Signal Line: {macd['signal_line']:.4f}")
            print(f"📊 Histogram: {macd['histogram']:.4f}")

            # Interpretation
            macd_interp = data["macd_interpretation"]
            print(
                f"🎯 Signal: {macd_interp['signal_type']} ({macd_interp['crossover']})"
            )

            # Overall recommendation
            rec = data["overall_recommendation"]
            print(f"🚀 Recommendation: {rec}")

            # Trading advice
            print()
            print("💡 Trading Insight:")

            if rec == "STRONG_BUY":
                print("   🔥 Strong bullish signals! Consider long positions")
            elif rec == "BUY":
                print("   📈 Bullish momentum detected")
            elif rec == "HOLD":
                print("   ⚪ Mixed signals - wait for clearer direction")
            elif rec == "SELL":
                print("   📉 Bearish momentum detected")
            elif rec == "STRONG_SELL":
                print("   ⚠️ Strong bearish signals - consider closing positions")

            return data

        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Details: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ API not running!")
        print(
            "Start it with: cd api && source .venv/bin/activate && uvicorn src.main:app --reload"
        )

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("🔍 SOL (Solana) MACD Analysis Tool")
    print("=" * 40)
    print()

    # Example with different timeframes
    timeframes = [("1h", "1 Hour"), ("4h", "4 Hours"), ("1d", "1 Day")]

    for interval, description in timeframes:
        print(f"\n📊 {description} Analysis:")
        get_sol_analysis(interval=interval)


if __name__ == "__main__":
    main()
