#!/usr/bin/env python3
"""
Build script for n8n-workflow-analyse-f.json
Multi-agent version: TA Agent + News Agent (parallel) → Supervisor Agent → Markdown

This script:
1. Reads n8n-workflow-analyse-e.json as base
2. Removes old nodes (Message a model, News Sentiment, Klines Tool, Current Price, Send a text message)
3. Adds new multi-agent pipeline nodes
4. Updates connections
5. Outputs to n8n-workflow-analyse-f.json
"""

import json
import uuid
from pathlib import Path

BASE_FILE = "docs/workflows/n8n-workflow-analyse-e.json"
OUTPUT_FILE = "docs/workflows/n8n-workflow-analyse-f.json"


def generate_id():
    return str(uuid.uuid4())


def main():
    # Read base workflow
    with open(BASE_FILE, "r") as f:
        wf = json.load(f)

    nodes = wf.get("nodes", [])
    connections = wf.get("connections", {})

    # ===== PHASE 1: Remove old nodes =====
    nodes_to_remove = [
        "Message a model",
        "News Sentiment",
        "Klines Tool",
        "Current Price",
        "Send a text message",
    ]

    nodes = [n for n in nodes if n["name"] not in nodes_to_remove]
    print(f"Removed {len(nodes_to_remove)} nodes")

    # ===== PHASE 2: Add new multi-agent pipeline nodes =====

    new_nodes = []

    # --- TA Agent Cluster ---
    # TA Ollama Model
    new_nodes.append(
        {
            "parameters": {"model": "glm-5"},
            "type": "@n8n/n8n-nodes-langchain.lmChatOllama",
            "typeVersion": 1,
            "position": [1024, 208],
            "id": generate_id(),
            "name": "TA Ollama Model",
            "credentials": {
                "ollamaApi": {"id": "URvt83r3fqd9q5Z7", "name": "Ollama account"}
            },
        }
    )

    # TA Output Parser
    new_nodes.append(
        {
            "parameters": {
                "schemaType": "fromJson",
                "jsonSchemaExample": json.dumps(
                    {
                        "market_regime": "bullish",
                        "regime_confidence": 75,
                        "trend_analysis": {
                            "short_term_15m": "bullish",
                            "medium_term_1h": "neutral",
                            "long_term_4h": "bearish",
                            "alignment": "mixed",
                        },
                        "key_levels": {"support": [1950.00], "resistance": [2050.00]},
                        "indicator_signals": {
                            "rsi_assessment": "RSI at 65 shows moderate bullish momentum but approaching overbought territory",
                            "macd_assessment": "MACD histogram turning positive with recent bullish crossover",
                            "sma_assessment": "Price above SMA 20 but below SMA 50 on 15m - neutral",
                        },
                        "confluence_score": "moderate",
                        "risk_factors": [
                            "Diverging timeframes",
                            "RSI approaching overbought",
                        ],
                    }
                ),
                "autoFix": False,
            },
            "type": "@n8n/n8n-nodes-langchain.outputParserStructured",
            "typeVersion": 1.3,
            "position": [896, 320],
            "id": generate_id(),
            "name": "TA Output Parser",
        }
    )

    # TA Agent
    ta_system_prompt = """You are an expert cryptocurrency technical analyst specializing in multi-timeframe analysis.

## Your Task
Analyze the provided technical indicator data for multiple timeframes and produce a structured analysis.

## Timeframe Hierarchy
- **15m (Short-term)**: Entry timing, immediate momentum
- **1h (Medium-term)**: Trend direction, swing setups
- **4h (Long-term)**: Market bias, structural levels

## Analysis Rules
1. **Timeframe Alignment**: Higher timeframes take precedence for trend direction
2. **Confluence**: Require at least 2-3 confirming indicators before signaling
3. **RSI Interpretation**:
   - <30 = oversold (potential long)
   - >70 = overbought (potential short)
   - 30-70 = neutral
4. **MACD Signals**:
   - Bullish: Histogram crosses above zero OR bullish divergence
   - Bearish: Histogram crosses below zero OR bearish divergence
5. **SMA Analysis**:
   - Price above SMA = bullish structure
   - Price below SMA = bearish structure
   - Golden cross (SMA 50 crosses above SMA 200) = bullish
   - Death cross (SMA 50 crosses below SMA 200) = bearish

## Output Requirements
Provide a JSON object with:
- market_regime: "bullish" | "bearish" | "neutral" | "mixed"
- regime_confidence: 0-100
- trend_analysis: Breakdown per timeframe
- key_levels: Support and resistance zones
- indicator_signals: Your interpretation of RSI, MACD, SMA
- confluence_score: "strong" | "moderate" | "weak"
- risk_factors: List of potential risks or conflicting signals

Be precise and data-driven. Use the exact values from the input."""
    ta_user_prompt = """## TECHNICAL ANALYSIS REQUEST
**Symbol:** {{ $json.dataIndicators[0].symbol }}
**Analysis Time:** {{ $now.format('yyyy-MM-dd HH:mm') }}

---

### Timeframe 1 ({{ $json.dataIndicators[0].interval }}) - [Short-term/Entry Timing]
** RSI:**
- Value: {{ $json.dataIndicators[0].rsi.value }}
- Signal: {{ $json.dataIndicators[0].rsi.signal }}

** MACD:**
- Line: {{ $json.dataIndicators[0].macd.macd_line }}
- Signal Line: {{ $json.dataIndicators[0].macd.signal_line }}
- Histogram: {{ $json.dataIndicators[0].macd.histogram }}
- Signal Type: {{ $json.dataIndicators[0].macd.signal_type }}
- Crossover: {{ $json.dataIndicators[0].macd.crossover }}

** SMA:**
- SMA 10: {{ $json.dataIndicators[0].sma.sma_10 }}
- SMA 20: {{ $json.dataIndicators[0].sma.sma_20 }}
- SMA 50: {{ $json.dataIndicators[0].sma.sma_50 }}
- Signal: {{ $json.dataIndicators[0].sma.signal }}

---

### Timeframe 2 ({{ $json.dataIndicators[1].interval }}) - [Medium-term/Trend Direction]
** RSI:**
- Value: {{ $json.dataIndicators[1].rsi.value }}
- Signal: {{ $json.dataIndicators[1].rsi.signal }}

** MACD:**
- Line: {{ $json.dataIndicators[1].macd.macd_line }}
- Signal Line: {{ $json.dataIndicators[1].macd.signal_line }}
- Histogram: {{ $json.dataIndicators[1].macd.histogram }}
- Signal Type: {{ $json.dataIndicators[1].macd.signal_type }}
- Crossover: {{ $json.dataIndicators[1].macd.crossover }}

** SMA:**
- SMA 20: {{ $json.dataIndicators[1].sma.sma_20 }}
- SMA 50: {{ $json.dataIndicators[1].sma.sma_50 }}
- SMA 200: {{ $json.dataIndicators[1].sma.sma_200 }}
- Signal: {{ $json.dataIndicators[1].sma.signal }}

---

### Timeframe 3 ({{ $json.dataIndicators[2].interval }}) - [Long-term/Market Bias]
** RSI:**
- Value: {{ $json.dataIndicators[2].rsi.value }}
- Signal: {{ $json.dataIndicators[2].rsi.signal }}

** MACD:**
- Line: {{ $json.dataIndicators[2].macd.macd_line }}
- Signal Line: {{ $json.dataIndicators[2].macd.signal_line }}
- Histogram: {{ $json.dataIndicators[2].macd.histogram }}
- Signal Type: {{ $json.dataIndicators[2].macd.signal_type }}
- Crossover: {{ $json.dataIndicators[2].macd.crossover }}

** SMA:**
- SMA 20: {{ $json.dataIndicators[2].sma.sma_20 }}
- SMA 50: {{ $json.dataIndicators[2].sma.sma_50 }}
- SMA 200: {{ $json.dataIndicators[2].sma.sma_200 }}
- Signal: {{ $json.dataIndicators[2].sma.signal }}

---

Provide your structured technical analysis in JSON format."""

    new_nodes.append(
        {
            "parameters": {
                "promptType": "define",
                "text": ta_user_prompt,
                "options": {
                    "systemMessage": ta_system_prompt,
                    "maxIterations": 10,
                    "returnIntermediateSteps": False,
                    "enableStreaming": True,
                },
                "hasOutputParser": True,
            },
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 3.1,
            "position": [1184, 272],
            "id": generate_id(),
            "name": "TA Agent",
        }
    )

    # --- News Agent Cluster ---
    # News Ollama Model
    new_nodes.append(
        {
            "parameters": {"model": "glm-5"},
            "type": "@n8n/n8n-nodes-langchain.lmChatOllama",
            "typeVersion": 1,
            "position": [1024, 480],
            "id": generate_id(),
            "name": "News Ollama Model",
            "credentials": {
                "ollamaApi": {"id": "URvt83r3fqd9q5Z7", "name": "Ollama account"}
            },
        }
    )

    # News Output Parser
    new_nodes.append(
        {
            "parameters": {
                "schemaType": "fromJson",
                "jsonSchemaExample": json.dumps(
                    {
                        "overall_sentiment": "bullish",
                        "sentiment_score": 0.65,
                        "bullish_count": 5,
                        "bearish_count": 2,
                        "neutral_count": 3,
                        "key_headlines": [
                            "Bitcoin ETF inflows hit $500M in single day",
                            "Major bank announces crypto custody service",
                        ],
                        "market_impact": "medium",
                        "sentiment_trend": "improving",
                        "summary": "Positive news momentum with institutional adoption themes dominating",
                    }
                ),
                "autoFix": False,
            },
            "type": "@n8n/n8n-nodes-langchain.outputParserStructured",
            "typeVersion": 1.3,
            "position": [896, 592],
            "id": generate_id(),
            "name": "News Output Parser",
        }
    )

    # News Sentiment Tool
    new_nodes.append(
        {
            "parameters": {
                "toolDescription": "Given the list of articles about crypto coin like BTC, ETH, SOL, etc. The articles are with their sentiment.\n",
                "url": "=http://api:8000/api/news/sentiment/{{ $('Translate to Symbol').item.json.coin }}",
                "options": {},
            },
            "type": "n8n-nodes-base.httpRequestTool",
            "typeVersion": 4.4,
            "position": [768, 688],
            "id": generate_id(),
            "name": "News Sentiment Tool",
        }
    )

    # News Agent
    news_system_prompt = """You are an expert cryptocurrency news analyst specializing in sentiment analysis and market impact assessment.

## Your Task
Analyze the provided news articles and sentiment data for a given cryptocurrency and produce a structured assessment.

## Analysis Framework
1. **Sentiment Classification**:
   - bullish: Positive price-moving news (partnerships, adoption, institutional interest, buy signals)
   - bearish: Negative price-moving news (regulatory concerns, hacks, selling pressure)
   - neutral: Informational news without clear price impact

2. **Scoring**:
   - sentiment_score: -1 (very bearish) to +1 (very bullish)
   - Use weighted average based on source credibility and recency

3. **Market Impact Assessment**:
   - high: Major announcements, regulatory news, large-scale adoption
   - medium: Product launches, partnerships, market updates
   - low: General news, social media discussions

4. **Trend Analysis**:
   - improving: More positive news than negative recently
   - declining: More negative news than positive recently
   - stable: Balanced news flow

## Output Requirements
Provide a JSON object with:
- overall_sentiment: "bullish" | "bearish" | "neutral"
- sentiment_score: -1.0 to 1.0
- bullish_count: number of bullish articles
- bearish_count: number of bearish articles
- neutral_count: number of neutral articles
- key_headlines: Most impactful headlines (up to 5)
- market_impact: "high" | "medium" | "low"
- sentiment_trend: "improving" | "declining" | "stable"
- summary: 1-2 sentence overview

Be precise and base your analysis on the actual data provided."""
    news_user_prompt = """## NEWS SENTIMENT ANALYSIS REQUEST
**Coin:** {{ $json.coin }}
**Symbol:** {{ $json.symbol }}
**Analysis Time:** {{ $now.format('yyyy-MM-dd HH:mm') }}

Analyze the news sentiment data for {{ $json.coin }} ({{ $json.symbol }}).

Use the News Sentiment Tool to fetch the latest news articles and their sentiment.

Provide your structured sentiment analysis in JSON format."""

    new_nodes.append(
        {
            "parameters": {
                "promptType": "define",
                "text": news_user_prompt,
                "options": {
                    "systemMessage": news_system_prompt,
                    "maxIterations": 10,
                    "returnIntermediateSteps": False,
                    "enableStreaming": True,
                },
                "hasOutputParser": True,
            },
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 3.1,
            "position": [1184, 544],
            "id": generate_id(),
            "name": "News Agent",
        }
    )

    # --- Merge Cluster ---
    # Merge Analyses
    new_nodes.append(
        {
            "parameters": {"mode": "append", "options": {}},
            "type": "n8n-nodes-base.merge",
            "typeVersion": 3.1,
            "position": [1408, 416],
            "id": generate_id(),
            "name": "Merge Analyses",
        }
    )

    # Prepare Supervisor Input
    prepare_code = """// Prepare combined input for Supervisor Agent
const allItems = $input.all();

const taItem = allItems.find(item => item.json.ta_analysis);
const newsItem = allItems.find(item => item.json.news_analysis);

const ta = taItem?.json;
const news = newsItem?.json;

// Extract symbol from various possible locations
const symbol = ta?.symbol || 
               ta?.dataIndicators?.[0]?.symbol || 
               news?.symbol || 
               "";

return {
  json: {
    symbol: symbol,
    coin: symbol.replace('USDT', ''),
    ta_analysis: ta || {},
    news_analysis: news || {}
  }
};
"""
    new_nodes.append(
        {
            "parameters": {"jsCode": prepare_code},
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1536, 416],
            "id": generate_id(),
            "name": "Prepare Supervisor Input",
        }
    )

    # --- Supervisor Cluster ---
    # Supervisor Gemini Model
    new_nodes.append(
        {
            "parameters": {"modelName": "models/gemini-2.5-flash"},
            "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
            "typeVersion": 1,
            "position": [2048, 544],
            "id": generate_id(),
            "name": "Supervisor Gemini Model",
        }
    )

    # Supervisor Agent
    supervisor_system_prompt = """You are a Senior Cryptocurrency Trading Strategist with elite expertise in multi-timeframe analysis, sentiment integration, and risk management.

## Your Role
Synthesize technical analysis and news sentiment into a coherent, actionable trading recommendation.

## Input Data
You will receive:
1. **Technical Analysis** (from TA Agent): Multi-timeframe indicator data with RSI, MACD, SMA analysis
2. **News Sentiment** (from News Agent): Market sentiment, key headlines, impact assessment

## Output Format
Produce a comprehensive Markdown report in this exact format:

```
Analyse for {SYMBOL} at {TIMESTAMP}

📊 MARKET STRUCTURE: [Bullish/Bearish/Neutral/Mixed with confidence %]

📋 TECHNICAL SUMMARY:
- Timeframe Alignment: [describe how 15m, 1h, 4h align]
- Key Levels: Support [list], Resistance [list]
- RSI: [value] - [signal]
- MACD: [signal type] - [crossover status]
- SMA: [price relative to SMAs]

📰 SENTIMENT OVERVIEW:
- Overall: [bullish/bearish/neutral] (score: X.X)
- Trend: [improving/declining/stable]
- Key Headlines:
  - [headline 1]
  - [headline 2]

🎯 TRADING RECOMMENDATION: 
- Action: [WAIT / LONG / SHORT / CLOSE POSITION]
- Entry Zone: [Price range or "Wait for trigger"]
- Stop Loss: [Price or percentage]
- Target 1 (2:1 R:R): [Price]
- Target 2 (3:1 R:R): [Price]

💡 SIGNAL BREAKDOWN:
- Confluence Score: [Strong/Moderate/Weak]
- Key Bullish Factors: [List 2-3]
- Key Bearish Factors: [List 2-3]
- Primary Risk: [Main concern]

⚠️ RISK WARNING:
[Specific conditions that could invalidate the setup]

📌 CONTEXT NOTES:
[Crypto-specific: volatility, 24/7 market, news sensitivity]
```

## Guidelines
1. **No Trade is Better Than a Bad Trade**: If signals conflict or confluence is weak, recommend WAITING
2. **Timeframe Hierarchy**: Respect 4h trend, use 1h for entries, 15m for timing
3. **Sentiment Integration**: Weight news impact appropriately - major news can override technicals
4. **Risk Management**: Always specify stop loss and risk/reward ratios
5. **Confirmation**: Require at least 2-3 confirming factors before signaling a trade"""
    supervisor_user_prompt = """## TRADING STRATEGY SYNTHESIS

Analyze the following combined data and produce a comprehensive trading report:

{{ JSON.stringify($json, null, 2) }}

Follow the output format exactly. Produce the final Markdown report."""

    new_nodes.append(
        {
            "parameters": {
                "promptType": "define",
                "text": supervisor_user_prompt,
                "options": {
                    "systemMessage": supervisor_system_prompt,
                    "maxIterations": 10,
                    "returnIntermediateSteps": False,
                    "enableStreaming": False,
                },
                "hasOutputParser": False,
            },
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 3.1,
            "position": [1856, 416],
            "id": generate_id(),
            "name": "Supervisor Agent",
        }
    )

    # Current Price (recycled from version E)
    new_nodes.append(
        {
            "parameters": {
                "toolDescription": 'Fetch current price of a cryto symbol (example: BTCUSDT, ETHUSDT, etc.). \n\nExample Output with input ETHUSDT:\n\n [\n  {\n    "symbol": "ETHUSDT",\n    "marketType": "futures",\n    "dataType": "markPriceKline",\n    "interval": "1m",\n    "limit": 1,\n    "currentPrice": "1980.80000000",\n    "klineCount": 1,\n    "klines": [\n      {\n        "openTime": 1771413360000,\n        "open": "1981.56000000",\n        "high": "1981.95000000",\n        "low": "1980.44558140",\n        "close": "1980.80000000",\n        "volume": "0",\n        "closeTime": 1771413419999,\n        "quoteVolume": "0",\n        "trades": 32,\n        "takerBuyBaseVolume": "0",\n        "takerBuyQuoteVolume": "0"\n      }\n    ],\n    "fetchedAt": "2026-02-18T11:16:41.224Z"\n  }\n]\n\nAnd the curren price is 1980.80000000',
                "apiSource": "direct",
                "marketType": "futures",
                "symbol": "={{ /*n8n-auto-generated-fromAI-override*/ $fromAI('Symbol', ``, 'string') }}",
                "interval": "1m",
                "limit": 1,
            },
            "type": "CUSTOM.binanceKlineTool",
            "typeVersion": 1,
            "position": [1920, 640],
            "id": generate_id(),
            "name": "Current Price",
            "credentials": {
                "binanceApi": {"id": "tmVGRcPSpJIYsaeS", "name": "Binance account"}
            },
        }
    )

    # Klines Tool (recycled from version E)
    new_nodes.append(
        {
            "parameters": {
                "toolDescription": "Fetch candlestick/kline data from Binance Spot or USD-M Futures API.\nExample Input: BTCUSDT, ETHUSDT, etc.",
                "apiSource": "direct",
                "marketType": "futures",
                "symbol": "={{ /*n8n-auto-generated-fromAI-override*/ $fromAI('Symbol', ``, 'string') }}",
                "interval": "1m",
                "limit": "={{ /*n8n-auto-generated-fromAI-override*/ $fromAI('Limit', ``, 'number') }}",
            },
            "type": "CUSTOM.binanceKlineTool",
            "typeVersion": 1,
            "position": [2048, 640],
            "id": generate_id(),
            "name": "Klines Tool",
            "credentials": {
                "binanceApi": {"id": "tmVGRcPSpJIYsaeS", "name": "Binance account"}
            },
        }
    )

    # Add all new nodes
    nodes.extend(new_nodes)
    print(f"Added {len(new_nodes)} new nodes")

    # ===== PHASE 3: Update connections =====
    # Build new connections dict
    new_connections = {}

    # Helper to add connection
    def add_connection(
        source, target, connection_type="main", output_index=0, input_index=0
    ):
        if source not in new_connections:
            new_connections[source] = {}
        if connection_type not in new_connections[source]:
            new_connections[source][connection_type] = []

        # Find existing or create new
        found = False
        for conn_list in new_connections[source][connection_type]:
            for conn in conn_list:
                if conn["node"] == target:
                    found = True
                    break
        if not found:
            new_connections[source][connection_type].append(
                [{"node": target, "type": connection_type, "index": input_index}]
            )

    # Get node names for reference
    node_names = {n["name"] for n in nodes}

    # --- Existing connections to keep ---
    # Triggers → Translate to Symbol
    add_connection("When chat message received", "Translate to Symbol")
    add_connection("My Telegram Channel", "Translate to Symbol")

    # Translate to Symbol → Intervals + Notify
    add_connection("Translate to Symbol", "Interval 15m")
    add_connection("Translate to Symbol", "Interval 1h")
    add_connection("Translate to Symbol", "Interval 4h")
    add_connection("Translate to Symbol", "Notify Analysis Start")

    # Intervals → Analyze workflows
    add_connection("Interval 15m", "Analyze 15m")
    add_connection("Interval 1h", "Analyze 1h")
    add_connection("Interval 4h", "Analyze 4h")

    # Analyze workflows → Merge Indicators
    add_connection("Analyze 15m", "Merge Indicators")
    add_connection("Analyze 1h", "Merge Indicators")
    add_connection("Analyze 4h", "Merge Indicators")

    # Merge Indicators → Sort by Interval
    add_connection("Merge Indicators", "Sort by Interval")

    # Sort by Interval → Aggregate
    add_connection("Sort by Interval", "Aggregate")

    # Aggregate → TA Agent (NEW)
    add_connection("Aggregate", "TA Agent")

    # Translate to Symbol → News Agent (NEW) - runs in parallel
    add_connection("Translate to Symbol", "News Agent")

    # TA Ollama Model → TA Agent (ai_languageModel)
    add_connection("TA Ollama Model", "TA Agent", "ai_languageModel")

    # TA Output Parser → TA Agent (ai_outputParser)
    add_connection("TA Output Parser", "TA Agent", "ai_outputParser")

    # News Ollama Model → News Agent (ai_languageModel)
    add_connection("News Ollama Model", "News Agent", "ai_languageModel")

    # News Output Parser → News Agent (ai_outputParser)
    add_connection("News Output Parser", "News Agent", "ai_outputParser")

    # News Sentiment Tool → News Agent (ai_tool)
    add_connection("News Sentiment Tool", "News Agent", "ai_tool")

    # TA Agent → Merge Analyses (main, input 0)
    add_connection("TA Agent", "Merge Analyses", "main", 0, 0)

    # News Agent → Merge Analyses (main, input 1)
    add_connection("News Agent", "Merge Analyses", "main", 0, 1)

    # Merge Analyses → Prepare Supervisor Input
    add_connection("Merge Analyses", "Prepare Supervisor Input")

    # Prepare Supervisor Input → Supervisor Agent
    add_connection("Prepare Supervisor Input", "Supervisor Agent")

    # Supervisor Gemini Model → Supervisor Agent (ai_languageModel)
    add_connection("Supervisor Gemini Model", "Supervisor Agent", "ai_languageModel")

    # Current Price → Supervisor Agent (ai_tool)
    add_connection("Current Price", "Supervisor Agent", "ai_tool")

    # Klines Tool → Supervisor Agent (ai_tool)
    add_connection("Klines Tool", "Supervisor Agent", "ai_tool")

    # Supervisor Agent → Markdown Binary
    add_connection("Supervisor Agent", "Markdown Binary")

    # Markdown Binary → Write to docs/analyse
    add_connection("Markdown Binary", "Write to docs/analyse")

    # Markdown Binary → Send a document
    add_connection("Markdown Binary", "Send a document")

    # Update workflow
    wf["nodes"] = nodes
    wf["connections"] = new_connections

    # Write output
    with open(OUTPUT_FILE, "w") as f:
        json.dump(wf, f, indent=2)

    print(f"Written to {OUTPUT_FILE}")
    print(f"Total nodes: {len(nodes)}")
    print(f"Total connection sources: {len(new_connections)}")

    # Summary
    print("\n=== Node Summary ===")
    for n in nodes:
        print(f"  {n['name']}: {n['type']}")

    print("\n=== Connection Summary ===")
    for src, targets in new_connections.items():
        for conn_type, conn_list in targets.items():
            for conn in conn_list:
                print(f"  {src} --({conn_type})-> {conn['node']}")


if __name__ == "__main__":
    main()
