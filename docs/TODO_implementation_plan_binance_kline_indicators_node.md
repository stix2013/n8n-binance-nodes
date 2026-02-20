
# TODO: Implementation Plan - BinanceKlineIndicators n8n Node

## 1. Scaffold the New Node

*   **Task:** Create a new n8n node file for compiling Binance Kline indicators.
*   **Location:** `nodes/@stix/n8n-nodes-binance-kline/nodes/BinanceKlineIndicators/BinanceKlineIndicators.node.ts`
*   **Details:**
    *   Define the `BinanceKlineIndicators` class implementing `INodeType`.
    *   Set `displayName` to "Binance Kline Indicators".
    *   Set `name` to `binanceKlineIndicators`.

## 2. Define Node Properties (Configuration)

*   **Task:** Configure user-facing parameters for the node.
*   **Details:**
    *   Add a required `string` property for `apiUrl` with a default value of `http://api:8000/api/ingest/analyze`.
    *   Add an optional "Parameters" section (using the `collection` type) that maps to the `AnalysisParameters` model in the API. This section should include:
        *   RSI Period (integer)
        *   MACD Fast Period (integer)
        *   MACD Slow Period (integer)
        *   MACD Signal Period (integer)
        *   SMA Enabled (boolean toggle)
        *   EMA Enabled (boolean toggle)

## 3. Implement the `execute` Method

*   **Task:** Define the core logic for fetching data, constructing the API payload, and making the request.
*   **Details:**
    *   Read the incoming items from the previous node (expected to be output from the `BinanceKline` node).
    *   Iterate over each input item.
    *   Construct the API payload that matches the `IngestRequest` model (`{"data": N8NNodeOutput, "parameters": AnalysisParameters}`).
    *   Retrieve the `apiUrl` from the node's parameters.
    *   Use `this.helpers.httpRequest` to perform a `POST` request to the configured `apiUrl` with the constructed JSON body.
    *   Return the API's response (which should conform to `IngestResponse`) as the output of the node.

## 4. Update `package.json`

*   **Task:** Register the new node within the n8n node package.
*   **Location:** `nodes/@stix/n8n-nodes-binance-kline/package.json`
*   **Details:**
    *   Add `"dist/nodes/BinanceKlineIndicators/BinanceKlineIndicators.node.js"` to the `n8n.nodes` array.

## 5. Build and Deploy

*   **Task:** Compile the node code and restart the n8n instance to recognize the new node.
*   **Steps:**
    *   Navigate to the node's directory: `cd nodes/@stix/n8n-nodes-binance-kline`
    *   Run the build command: `bun run build`
    *   Stop the Docker environment: `bun stop`
    *   Start the Docker environment: `bun start`
    *   Provide instructions on how to test the new node in the n8n UI.
