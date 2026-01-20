#!/usr/bin/env python3
"""
Demo script for technical indicators functionality.
This script demonstrates RSI and MACD calculations with sample data.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from utils.indicators import TechnicalIndicators
from datetime import datetime


def generate_sample_prices(symbol: str = "BTCUSDT", days: int = 30) -> list:
    """Generate realistic sample price data for testing."""
    import random

    # Start with a base price
    base_price = 45000.0 if "BTC" in symbol else 2500.0

    prices = [base_price]

    # Generate realistic price movements
    for i in range(days):
        # Add some volatility and trend
        daily_change = random.uniform(-0.05, 0.05)  # ±5% daily change
        trend = 0.001 * i  # Slight upward trend

        new_price = prices[-1] * (1 + daily_change + trend)
        prices.append(new_price)

    return prices


def demonstrate_rsi():
    """Demonstrate RSI calculation and interpretation."""
    print("=== RSI (Relative Strength Index) Demo ===\n")

    # Generate sample data
    prices = generate_sample_prices("BTCUSDT", 30)
    print(f"Sample data: {len(prices)} price points")
    print(f"Price range: ${min(prices):.2f} - ${max(prices):.2f}")
    print()

    # Calculate RSI with different periods
    for period in [14, 21, 30]:
        rsi = TechnicalIndicators.calculate_rsi(prices, period)
        signal = TechnicalIndicators.generate_rsi_signal(rsi)

        print(f"RSI ({period} periods): {rsi:.2f}")
        print(f"Signal: {signal}")

        # Interpretation
        if signal == "OVERSOLD":
            print("→ Potential BUY opportunity (market may be oversold)")
        elif signal == "OVERBOUGHT":
            print("→ Potential SELL opportunity (market may be overbought)")
        else:
            print("→ HOLD - Market in neutral zone")
        print()


def demonstrate_macd():
    """Demonstrate MACD calculation and interpretation."""
    print("=== MACD (Moving Average Convergence Divergence) Demo ===\n")

    # Generate sample data with trend
    prices = generate_sample_prices("BTCUSDT", 50)
    print(f"Sample data: {len(prices)} price points")
    print(f"Price range: ${min(prices):.2f} - ${max(prices):.2f}")
    print()

    # Calculate MACD with standard parameters
    macd_data = TechnicalIndicators.calculate_macd(prices)
    signal_type, crossover = TechnicalIndicators.generate_macd_signal(macd_data)

    print(f"MACD Line: {macd_data['macd_line']:.4f}")
    print(f"Signal Line: {macd_data['signal_line']:.4f}")
    print(f"Histogram: {macd_data['histogram']:.4f}")
    print()
    print(f"Signal Type: {signal_type}")
    print(f"Crossover: {crossover}")

    # Interpretation
    if signal_type == "BULLISH":
        print("→ Positive momentum - consider BUY signals")
    elif signal_type == "BEARISH":
        print("→ Negative momentum - consider SELL signals")
    else:
        print("→ No clear trend - HOLD")
    print()


def demonstrate_combined_analysis():
    """Demonstrate combined RSI + MACD analysis."""
    print("=== Combined RSI + MACD Analysis ===\n")

    # Generate sample data
    prices = generate_sample_prices("BTCUSDT", 50)

    # Calculate both indicators
    rsi = TechnicalIndicators.calculate_rsi(prices, 14)
    rsi_signal = TechnicalIndicators.generate_rsi_signal(rsi)

    macd_data = TechnicalIndicators.calculate_macd(prices)
    macd_signal, macd_crossover = TechnicalIndicators.generate_macd_signal(macd_data)

    # Generate overall recommendation
    recommendation = TechnicalIndicators.generate_overall_recommendation(
        rsi_signal, macd_signal, macd_crossover
    )

    print("Analysis Results:")
    print("-" * 20)
    print(f"Current Price: ${prices[-1]:.2f}")
    print(f"RSI (14): {rsi:.2f} ({rsi_signal})")
    print(f"MACD: {macd_signal} ({macd_crossover})")
    print()
    print(f"📊 Overall Recommendation: {recommendation}")
    print()

    # Detailed interpretation
    print("Detailed Interpretation:")
    print("-" * 25)

    if recommendation == "STRONG_BUY":
        print("🔥 STRONG BUY: Both RSI and MACD indicate bullish momentum")
        print("   → Consider opening long positions")
    elif recommendation == "STRONG_SELL":
        print("⚠️  STRONG SELL: Both RSI and MACD indicate bearish momentum")
        print("   → Consider closing positions or shorting")
    elif recommendation == "BUY":
        print("📈 BUY: At least one indicator shows bullish signals")
        print("   → Consider buying with caution")
    elif recommendation == "SELL":
        print("📉 SELL: At least one indicator shows bearish signals")
        print("   → Consider selling or taking profits")
    else:
        print("⏸️  HOLD: Mixed or neutral signals")
        print("   → Wait for clearer signals before trading")


def demonstrate_parameter_sensitivity():
    """Demonstrate how different parameters affect calculations."""
    print("=== Parameter Sensitivity Analysis ===\n")

    # Generate sample data
    prices = generate_sample_prices("ETHUSDT", 100)

    # Test different RSI periods
    print("RSI Period Sensitivity:")
    print("-" * 25)
    for period in [7, 14, 21, 30]:
        rsi = TechnicalIndicators.calculate_rsi(prices, period)
        signal = TechnicalIndicators.generate_rsi_signal(rsi)
        print(f"Period {period:2d}: RSI = {rsi:5.1f} ({signal})")
    print()

    # Test different MACD periods
    print("MACD Parameter Sensitivity:")
    print("-" * 30)
    test_configs = [
        (5, 13, 5),  # Fast MACD
        (12, 26, 9),  # Standard MACD
        (19, 39, 9),  # Slow MACD
    ]

    for fast, slow, signal in test_configs:
        try:
            macd_data = TechnicalIndicators.calculate_macd(prices, fast, slow, signal)
            signal_type, crossover = TechnicalIndicators.generate_macd_signal(macd_data)
            print(
                f"({fast:2d},{slow:2d},{signal:2d}): {signal_type:8s} ({crossover:6s})"
            )
        except Exception as e:
            print(f"({fast:2d},{slow:2d},{signal:2d}): Error - {e}")


def demonstrate_validation():
    """Demonstrate data validation."""
    print("=== Data Validation Demo ===\n")

    # Test various edge cases
    test_cases = [
        ("Empty data", []),
        ("Insufficient data", [100.0, 101.0, 102.0]),  # Only 3 points
        ("Zero prices", [0.0, 0.0, 0.0]),
        ("Negative prices", [-100.0, 200.0, 300.0]),
        ("Identical prices", [100.0] * 30),
        ("Valid data", [100.0 + i for i in range(30)]),
    ]

    for description, prices in test_cases:
        print(f"Testing: {description}")
        try:
            TechnicalIndicators.validate_price_data(prices, min_candles=30)
            print("✅ PASSED: Data validation successful")
        except ValueError as e:
            print(f"❌ FAILED: {e}")
        print()


def main():
    """Main demo function."""
    print("🔬 Technical Indicators Demo")
    print("=" * 50)
    print("This demo showcases RSI and MACD calculations")
    print("for cryptocurrency price analysis.")
    print()

    # Run all demonstrations
    demonstrate_rsi()
    print("\n" + "=" * 60 + "\n")

    demonstrate_macd()
    print("\n" + "=" * 60 + "\n")

    demonstrate_combined_analysis()
    print("\n" + "=" * 60 + "\n")

    demonstrate_parameter_sensitivity()
    print("\n" + "=" * 60 + "\n")

    demonstrate_validation()

    print("\n🎯 Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("• RSI calculation with configurable periods")
    print("• MACD calculation (line, signal, histogram)")
    print("• Signal generation (OVERSOLD/OVERBOUGHT/BULLISH/BEARISH)")
    print("• Combined analysis and trading recommendations")
    print("• Parameter sensitivity analysis")
    print("• Data validation and error handling")
    print("\n🚀 Ready for production use!")


if __name__ == "__main__":
    main()
