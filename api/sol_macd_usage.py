#!/usr/bin/env python3
"""
Example: How to use MACD analysis for SOL (Solana)
"""

def show_sol_usage_examples():
    print("=== MACD Analysis for SOL (Solana) ===")
    print()
    
    print("1. FULL ANALYSIS (RSI + MACD + Recommendations)")
    print("   Endpoint: GET /api/indicators/analysis")
    print("   Example curl:")
    print('   curl "http://localhost:8000/api/indicators/analysis?symbol=SOLUSDT&interval=1h&limit=100"')
    print()
    
    print("   Example Python code:")
    print('''
import requests

response = requests.get("http://localhost:8000/api/indicators/analysis", params={
    "symbol": "SOLUSDT",
    "interval": "1h", 
    "limit": 100
})

if response.status_code == 200:
    data = response.json()
    print(f"Current Price: ${data['current_price']:.2f}")
    print(f"RSI: {data['rsi']['value']:.2f} ({data['rsi']['signal']})")
    print(f"MACD Line: {data['macd']['macd_line']:.4f}")
    print(f"MACD Signal: {data['macd']['signal_line']:.4f}")
    print(f"MACD Histogram: {data['macd']['histogram']:.4f}")
    print(f"Recommendation: {data['overall_recommendation']}")
else:
    print(f"Error: {response.status_code}")
    ''')
    print()
    
    print("2. SINGLE MACD ANALYSIS")
    print("   Endpoint: GET /api/indicators/macd")
    print("   Example curl:")
    print('   curl "http://localhost:8000/api/indicators/macd?symbol=SOLUSDT&interval=4h"')
    print()
    
    print("3. CUSTOM PARAMETERS")
    print("   You can customize the MACD calculation periods:")
    print('   curl "http://localhost:8000/api/indicators/analysis?symbol=SOLUSDT&interval=4h&macd_fast=5&macd_slow=13&macd_signal=5"')
    print()
    
    print("4. INTERPRETING THE RESULTS:")
    print("   - MACD Line > Signal Line: BULLISH (Consider BUY)")
    print("   - MACD Line < Signal Line: BEARISH (Consider SELL)")
    print("   - Histogram > 0: Momentum increasing")
    print("   - Histogram < 0: Momentum decreasing")
    print()
    
    print("5. RECOMMENDATION SIGNALS:")
    print("   - STRONG_BUY: RSI oversold + MACD bullish crossover")
    print("   - BUY: At least one bullish signal")
    print("   - HOLD: Mixed or neutral signals")
    print("   - SELL: At least one bearish signal") 
    print("   - STRONG_SELL: RSI overbought + MACD bearish crossover")

if __name__ == "__main__":
    show_sol_usage_examples()
