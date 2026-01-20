#!/usr/bin/env python3
"""
Practical example: Getting real SOL MACD analysis
Make sure you have the API running: uvicorn src.main:app --reload
"""

import requests
import json

def analyze_sol():
    """Example of getting MACD analysis for SOLUSDT"""
    
    print("=== SOL (Solana) MACD Analysis Example ===")
    print()
    
    # API endpoint
    base_url = "http://localhost:8000"
    
    # Parameters for SOL analysis
    params = {
        "symbol": "SOLUSDT",
        "interval": "1h",  # 1-hour candles
        "limit": 100       # Get 100 candles for analysis
    }
    
    print("📊 Request Parameters:")
    print(f"   Symbol: {params['symbol']}")
    print(f"   Interval: {params['interval']}")
    print(f"   Limit: {params['limit']} candles")
    print()
    
    try:
        # Make the request
        print("🔄 Making API request...")
        response = requests.get(f"{base_url}/api/indicators/analysis", params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Analysis Complete!")
            print()
            
            # Display results
            print("📈 SOL Analysis Results:")
            print(f"   Current Price: ${data['current_price']:,.2f}")
            print()
            
            # RSI Analysis
            print("📊 RSI Analysis:")
            print(f"   RSI Value: {data['rsi']['value']:.2f}")
            print(f"   Signal: {data['rsi']['signal']}")
            
            # RSI Interpretation
            rsi_value = data['rsi']['value']
            if rsi_value < 30:
                rsi_interpretation = "🔵 Oversold (Potential BUY opportunity)"
            elif rsi_value > 70:
                rsi_interpretation = "🔴 Overbought (Potential SELL opportunity)"
            else:
                rsi_interpretation = "⚪ Neutral"
            print(f"   Interpretation: {rsi_interpretation}")
            print()
            
            # MACD Analysis
            print("📊 MACD Analysis:")
            print(f"   MACD Line: {data['macd']['macd_line']:.4f}")
            print(f"   Signal Line: {data['macd']['signal_line']:.4f}")
            print(f"   Histogram: {data['macd']['histogram']:.4f}")
            
            # MACD Interpretation
            macd_line = data['macd']['macd_line']
            signal_line = data['macd']['signal_line']
            histogram = data['macd']['histogram']
            
            if macd_line > signal_line:
                macd_interpretation = "🟢 Bullish (MACD above Signal)"
            else:
                macd_interpretation = "🔴 Bearish (MACD below Signal)"
            
            if histogram > 0:
                momentum = "📈 Increasing momentum"
            else:
                momentum = "📉 Decreasing momentum"
                
            print(f"   Signal: {data['macd_interpretation']['signal_type']}")
            print(f"   Interpretation: {macd_interpretation}")
            print(f"   Momentum: {momentum}")
            print()
            
            # Overall Recommendation
            recommendation = data['overall_recommendation']
            print(f"🎯 Overall Recommendation: {recommendation}")
            
            # Recommendation interpretation
            if recommendation == "STRONG_BUY":
                rec_interpretation = "🔥 Strong bullish signals detected!"
            elif recommendation == "BUY":
                rec_interpretation = "📈 Bullish momentum - consider buying"
            elif recommendation == "SELL":
                rec_interpretation = "📉 Bearish momentum - consider selling"
            elif recommendation == "STRONG_SELL":
                rec_interpretation = "⚠️ Strong bearish signals detected!"
            else:
                rec_interpretation = "⚪ Mixed signals - hold position"
            
            print(f"   {rec_interpretation}")
            print()
            
            # Additional info
            print(f"📊 Data Quality:")
            print(f"   Candles Analyzed: {data['candles_analyzed']}")
            print(f"   Analysis Time: {data['analysis_timestamp']}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API")
        print("   Make sure the API is running:")
        print("   cd api && source .venv/bin/activate")
        print("   uvicorn src.main:app --reload")
        print()
        print("🔧 To start the API:")
        print("   1. Open terminal")
        print("   2. cd api")
        print("   3. source .venv/bin/activate")
        print("   4. uvicorn src.main:app --reload")
        print("   5. Run this script again")

if __name__ == "__main__":
    analyze_sol()
