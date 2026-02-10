"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BinanceKline = void 0;
const n8n_workflow_1 = require("n8n-workflow");
class BinanceKline {
    constructor() {
        this.description = {
            displayName: 'Binance Kline',
            name: 'binanceKline',
            icon: { light: 'file:binance-kline.svg', dark: 'file:binance-kline.dark.svg' },
            group: ['input'],
            version: 1,
            subtitle: '={{$parameter["symbolSource"] === "watchlist" ? "Watchlist" : $parameter["symbol"]}}',
            description: 'Fetch candlestick/kline data from Binance API',
            defaults: {
                name: 'Binance Kline',
            },
            inputs: [n8n_workflow_1.NodeConnectionTypes.Main],
            outputs: [n8n_workflow_1.NodeConnectionTypes.Main],
            credentials: [
                {
                    name: 'binanceApi',
                    required: true,
                },
            ],
            usableAsTool: true,
            properties: [
                {
                    displayName: 'Symbol Source',
                    name: 'symbolSource',
                    type: 'options',
                    options: [
                        {
                            name: 'Single Symbol',
                            value: 'single',
                            description: 'Fetch data for a single trading pair',
                        },
                        {
                            name: 'Watchlist',
                            value: 'watchlist',
                            description: 'Fetch data for all symbols in your credentials watchlist',
                        },
                    ],
                    default: 'single',
                    description: 'Choose whether to fetch data for a single symbol or your entire watchlist',
                },
                {
                    displayName: 'Symbol',
                    name: 'symbol',
                    type: 'string',
                    default: 'BTCUSDT',
                    placeholder: 'e.g. BTCUSDT, ETHUSDT',
                    description: 'The trading pair symbol',
                    displayOptions: {
                        show: {
                            symbolSource: ['single'],
                        },
                    },
                },
                {
                    displayName: 'Interval',
                    name: 'interval',
                    type: 'options',
                    options: [
                        { name: '1 Day', value: '1d' },
                        { name: '1 Hour', value: '1h' },
                        { name: '1 Minute', value: '1m' },
                        { name: '1 Month', value: '1M' },
                        { name: '1 Week', value: '1w' },
                        { name: '12 Hours', value: '12h' },
                        { name: '15 Minutes', value: '15m' },
                        { name: '2 Hours', value: '2h' },
                        { name: '3 Days', value: '3d' },
                        { name: '3 Minutes', value: '3m' },
                        { name: '30 Minutes', value: '30m' },
                        { name: '4 Hours', value: '4h' },
                        { name: '5 Minutes', value: '5m' },
                        { name: '6 Hours', value: '6h' },
                        { name: '8 Hours', value: '8h' },
                    ],
                    default: '1h',
                    description: 'Kline/candlestick interval',
                },
                {
                    displayName: 'Limit',
                    name: 'limit',
                    type: 'number',
                    typeOptions: {
                        minValue: 1,
                        maxValue: 1000,
                    },
                    default: 50,
                    description: 'Max number of results to return',
                },
            ],
        };
    }
    async execute() {
        const items = this.getInputData();
        const returnData = [];
        const credentials = await this.getCredentials('binanceApi');
        for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
            try {
                const symbolSource = this.getNodeParameter('symbolSource', itemIndex, 'single');
                const interval = this.getNodeParameter('interval', itemIndex, '1h');
                const limit = this.getNodeParameter('limit', itemIndex, 50);
                let symbols = [];
                if (symbolSource === 'watchlist') {
                    const watchlist = credentials.watchlist || '';
                    if (!watchlist || watchlist.trim() === '') {
                        throw new n8n_workflow_1.NodeOperationError(this.getNode(), 'Watchlist is empty. Please add symbols to your Binance API credentials watchlist.', { itemIndex });
                    }
                    symbols = watchlist
                        .split(',')
                        .map((s) => s.trim().toUpperCase())
                        .filter((s) => s.length > 0);
                    if (symbols.length === 0) {
                        throw new n8n_workflow_1.NodeOperationError(this.getNode(), 'No valid symbols found in watchlist. Please check your watchlist format (e.g., BTCUSDT, ETHUSDT, SOLUSDT).', { itemIndex });
                    }
                    this.logger.debug(`Watchlist mode: Fetching data for ${symbols.length} symbols: ${symbols.join(', ')}`);
                    symbols = watchlist
                        .split(',')
                        .map((s) => s.trim().toUpperCase())
                        .filter((s) => s.length > 0);
                    if (symbols.length === 0) {
                        throw new n8n_workflow_1.NodeOperationError(this.getNode(), 'No valid symbols found in watchlist.', { itemIndex });
                    }
                }
                else {
                    const symbol = this.getNodeParameter('symbol', itemIndex, 'BTCUSDT');
                    symbols = [symbol.toUpperCase()];
                }
                for (const symbol of symbols) {
                    const baseUrl = process.env.N8N_BINANCE_API_URL || 'http://api:8000';
                    const response = await this.helpers.httpRequest({
                        method: 'GET',
                        url: `${baseUrl}/api/binance/price`,
                        qs: {
                            symbol,
                            interval,
                            limit,
                        },
                        timeout: 30000,
                    });
                    const priceResponse = response;
                    const klines = priceResponse.data.map((k) => ({
                        openTime: new Date(k.open_time).getTime(),
                        open: k.open_price.toString(),
                        high: k.high_price.toString(),
                        low: k.low_price.toString(),
                        close: k.close_price.toString(),
                        volume: k.volume.toString(),
                        closeTime: new Date(k.close_time).getTime(),
                        quoteVolume: k.quote_asset_volume.toString(),
                        trades: k.number_of_trades,
                        takerBuyBaseVolume: k.taker_buy_base_asset_volume.toString(),
                        takerBuyQuoteVolume: k.taker_buy_quote_asset_volume.toString(),
                    }));
                    const latestKline = klines[klines.length - 1];
                    returnData.push({
                        json: {
                            symbol,
                            interval,
                            limit,
                            currentPrice: (latestKline === null || latestKline === void 0 ? void 0 : latestKline.close) || null,
                            klineCount: klines.length,
                            klines,
                            fetchedAt: new Date().toISOString(),
                        },
                        pairedItem: { item: itemIndex },
                    });
                }
            }
            catch (error) {
                if (this.continueOnFail()) {
                    returnData.push({
                        json: {
                            error: error.message,
                        },
                        pairedItem: { item: itemIndex },
                    });
                    continue;
                }
                if (error.context) {
                    error.context.itemIndex = itemIndex;
                    throw error;
                }
                throw new n8n_workflow_1.NodeOperationError(this.getNode(), error, {
                    itemIndex,
                });
            }
        }
        return [returnData];
    }
}
exports.BinanceKline = BinanceKline;
//# sourceMappingURL=BinanceKline.node.js.map