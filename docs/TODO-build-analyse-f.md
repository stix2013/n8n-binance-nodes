# TODO: Build n8n-workflow-analyse-f.json - Multi-Agent Version

## Status: PENDING IMPLEMENTATION

## Goal
Create `docs/workflows/n8n-workflow-analyse-f.json` — a multi-agent version of the Binance analysis workflow using the Parallel Agents + Supervisor pattern:
- **Technical Analysis Agent** (Ollama) → structured JSON
- **News Sentiment Agent** (Ollama) → structured JSON
- **Trading Strategy Supervisor Agent** (Google Gemini) → free-form Markdown report

## Base Version
- **Source:** `docs/workflows/n8n-workflow-analyse-e.json` (current production version)
- **Deployed Sub-workflow ID:** `1X1ODf4tA0Vi8SsT`

---

## Architecture

```
UNCHANGED (16 nodes):
  Triggers → Translate to Symbol → [Interval 15m/1h/4h + Notify] →
  Analyze 15m/1h/4h → Merge Indicators → Sort → Aggregate →
  ... → Markdown Binary → [Send Doc + Write File]

NEW MULTI-AGENT PIPELINE (14 nodes):

  Translate to Symbol ─┬─→ [Intervals → ... → Aggregate] → TA Agent ──────→ Merge Analyses
                       │                                      ↑ ai_llm        ↑ (input 0)
                       │                                  TA Ollama Model     │
                       │                                      ↑ ai_parser    │
                       │                                  TA Output Parser   │
                       │                                                     │
                       └─→ News Agent ──────────────────────────────────────→ Merge Analyses
                            ↑ ai_llm                                          (input 1)
                        News Ollama Model                                       │
                            ↑ ai_parser                                         ▼
                        News Output Parser                              Prepare Input (Code)
                            ↑ ai_tool                                           │
                        News Sentiment Tool                                     ▼
                                                                        Supervisor Agent
                                                                          ↑ ai_llm
                                                                    Gemini 2.5 Flash
                                                                          ↑ ai_tool  ↑ ai_tool
                                                                    Current Price   Klines Tool
                                                                              │
                                                                              ▼
                                                                      Markdown Binary → ...
```

---

## Implementation Phases

### Phase 1: Python Build Script
- Read `n8n-workflow-analyse-e.json` as base
- Use Python to safely handle n8n expressions with `$`, `{{`, `}}`
- Output to `docs/workflows/n8n-workflow-analyse-f.json`

### Phase 2: Remove Old Nodes (5)
| Node | Type | Why |
|------|------|-----|
| `Message a model` | `@n8n/n8n-nodes-langchain.ollama` | Replaced by 3 AI Agents |
| `News Sentiment` | `n8n-nodes-base.httpRequestTool` | Moved to News Agent cluster |
| `Klines Tool` | `CUSTOM.binanceKlineTool` | Moved to Supervisor cluster |
| `Current Price` | `CUSTOM.binanceKlineTool` | Moved to Supervisor cluster |
| `Send a text message` | `n8n-nodes-base.telegram` | Replaced by Aggregate → Notify path |

### Phase 3: Add 14 New Nodes

#### TA Agent Cluster (3 nodes)
1. **TA Agent** (`@n8n/n8n-nodes-langchain.agent` v3.1)
   - `promptType: "define"`
   - `hasOutputParser: true`
   - System Prompt: Expert TA analyst with timeframe hierarchy rules
   - User Prompt: The indicator data template from version E (without output format section)

2. **TA Ollama Model** (`@n8n/n8n-nodes-langchain.lmChatOllama` v1)
   - `model: "glm-5"`
   - Credentials: Ollama account

3. **TA Output Parser** (`@n8n/n8n-nodes-langchain.outputParserStructured` v1.3)
   - `schemaType: "fromJson"`
   - JSON Schema:
     ```json
     {
       "market_regime": "bullish",
       "regime_confidence": 75,
       "trend_analysis": {
         "short_term_15m": "bullish",
         "medium_term_1h": "neutral",
         "long_term_4h": "bearish",
         "alignment": "mixed"
       },
       "key_levels": {
         "support": [1950.00],
         "resistance": [2050.00]
       },
       "indicator_signals": {
         "rsi_assessment": "...",
         "macd_assessment": "...",
         "sma_assessment": "..."
       },
       "confluence_score": "moderate",
       "risk_factors": ["Diverging timeframes"]
     }
     ```

#### News Agent Cluster (4 nodes)
4. **News Agent** (`@n8n/n8n-nodes-langchain.agent` v3.1)
   - `promptType: "define"`
   - `hasOutputParser: true`
   - System Prompt: Crypto news sentiment analyst
   - User Prompt: `Analyze news for {{ $json.coin }} ({{ $json.symbol }})`

5. **News Ollama Model** (`@n8n/n8n-nodes-langchain.lmChatOllama` v1)
   - `model: "glm-5"`
   - Credentials: Ollama account

6. **News Output Parser** (`@n8n/n8n-nodes-langchain.outputParserStructured` v1.3)
   - `schemaType: "fromJson"`
   - JSON Schema:
     ```json
     {
       "overall_sentiment": "bullish",
       "sentiment_score": 0.65,
       "bullish_count": 5,
       "bearish_count": 2,
       "neutral_count": 3,
       "key_headlines": ["Headline 1"],
       "market_impact": "medium",
       "sentiment_trend": "improving",
       "summary": "Brief overview"
     }
     ```

7. **News Sentiment Tool** (`n8n-nodes-base.httpRequestTool` v4.4)
   - Same config as version E's "News Sentiment"
   - URL: `=http://api:8000/api/news/sentiment/{{ $('Translate to Symbol').item.json.coin }}`

#### Merge Cluster (2 nodes)
8. **Merge Analyses** (`n8n-nodes-base.merge` v3.1)
   - `mode: "append"`
   - Collects both agent outputs as 2 items

9. **Prepare Supervisor Input** (`n8n-nodes-base.code` v2)
   - Combines items into: `{ symbol, ta_analysis, news_analysis }`
   - JavaScript:
     ```javascript
     const ta = $input.first().json.ta_analysis;
     const news = $input.all()[1]?.json.news_analysis;
     return {
       json: {
         symbol: ta?.symbol || $input.first().json.dataIndicators?.[0]?.symbol,
         ta_analysis: ta,
         news_analysis: news
       }
     };
     ```

#### Supervisor Cluster (3 nodes)
10. **Supervisor Agent** (`@n8n/n8n-nodes-langchain.agent` v3.1)
    - `promptType: "define"`
    - `hasOutputParser: false`
    - System Prompt: Senior trading strategist with markdown output format from version E
    - User Prompt: `{{ JSON.stringify($json, null, 2) }}`
    - `options.enableStreaming: false`

11. **Supervisor Gemini Model** (`@n8n/n8n-nodes-langchain.lmChatGoogleGemini` v1)
    - `modelName: "models/gemini-2.5-flash"`
    - Credentials: Google Gemini (to be created by user after import)

12. **Current Price** (`CUSTOM.binanceKlineTool` v1)
    - Recycled config from version E

13. **Klines Tool** (`CUSTOM.binanceKlineTool` v1)
    - Recycled config from version E

14. **Markdown Report** (reuses existing node)
    - Already in version E as "Markdown Binary"

### Phase 4: Connection Wiring

**Remove 6 connections:**
- Aggregate → Message a model
- Aggregate → Send a text message
- Message a model → Markdown Binary
- News Sentiment → Message a model (ai_tool)
- Klines Tool → Message a model (ai_tool)
- Current Price → Message a model (ai_tool)

**Add 14 connections:**
| From | To | Type |
|------|----|------|
| Aggregate | TA Agent | main |
| Translate to Symbol | News Agent | main |
| TA Ollama Model | TA Agent | ai_languageModel |
| TA Output Parser | TA Agent | ai_outputParser |
| News Ollama Model | News Agent | ai_languageModel |
| News Output Parser | News Agent | ai_outputParser |
| News Sentiment Tool | News Agent | ai_tool |
| TA Agent | Merge Analyses | main (input 0) |
| News Agent | Merge Analyses | main (input 1) |
| Merge Analyses | Prepare Supervisor Input | main |
| Prepare Supervisor Input | Supervisor Agent | main |
| Supervisor Gemini Model | Supervisor Agent | ai_languageModel |
| Current Price | Supervisor Agent | ai_tool |
| Klines Tool | Supervisor Agent | ai_tool |
| Supervisor Agent | Markdown Binary | main |

### Phase 5: Validate
- Validate JSON structure
- Check all node IDs are unique
- Verify all connection targets exist

### Phase 6: Post-Import Setup
After importing into n8n:
1. Create a Google Gemini API credential in n8n
2. Assign it to the "Supervisor Gemini Model" node
3. Verify Ollama credentials are auto-linked on the 2 Ollama nodes
4. Save and activate the workflow

---

## Credentials Required

| Credential | ID in Version E | Used By |
|------------|-----------------|---------|
| Binance API | `tmVGRcPSpJIYsaeS` | Klines Tool, Current Price |
| Telegram API | `O5JL1UG87JJ1GySx` | Send a document, Write to docs/analyse, Notify Analysis Start |
| Ollama API | `URvt83r3fqd9q5Z7` | TA Ollama Model, News Ollama Model |
| **Google Gemini** | **NEW (to create)** | Supervisor Gemini Model |

---

## Design Decisions (Confirmed by User)

1. **News Agent starts from:** Translate to Symbol (max parallelism, runs while indicators compute)
2. **Supervisor has tools:** Yes, both Current Price and Klines Tool
3. **Gemini model:** `gemini-2.5-flash` (latest default)
4. **TA Agent has tools:** No — works purely from pre-computed indicators

---

## Files

- **Base:** `docs/workflows/n8n-workflow-analyse-e.json`
- **Output:** `docs/workflows/n8n-workflow-analyse-f.json`
- **Sub-workflow:** `docs/workflows/n8n-subworkflow-kline-analyze.json` (ID: `1X1ODf4tA0Vi8SsT`)

---

## Node Count

| Version | Nodes | Change |
|---------|-------|--------|
| E | 21 | — |
| F | 30 | +9 (16 kept + 14 new - 5 removed) |

---

## References

- n8n AI Agent node: `@n8n/n8n-nodes-langchain.agent` v3.1
- Ollama Chat Model: `@n8n/n8n-nodes-langchain.lmChatOllama` v1
- Google Gemini Chat Model: `@n8n/n8n-nodes-langchain.lmChatGoogleGemini` v1
- Structured Output Parser: `@n8n/n8n-nodes-langchain.outputParserStructured` v1.3
- Binance Kline Tool: `CUSTOM.binanceKlineTool` v1
- News Sentiment Tool: `n8n-nodes-base.httpRequestTool` v4.4
- Merge: `n8n-nodes-base.merge` v3.1
- Code: `n8n-nodes-base.code` v2
