import type {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	IHttpRequestMethods,
} from 'n8n-workflow';
import { NodeConnectionTypes, NodeOperationError } from 'n8n-workflow';

interface TickerPriceResponse {
	symbol: string;
	price: string;
}

interface Ticker24hrResponse {
	symbol: string;
	priceChange: string;
	priceChangePercent: string;
	weightedAvgPrice: string;
	lastPrice: string;
	lastQty: string;
	openPrice: string;
	highPrice: string;
	lowPrice: string;
	volume: string;
	quoteVolume: string;
	openTime: number;
	closeTime: number;
	firstId: number;
	lastId: number;
	count: number;
}

export class BinanceTicker implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Binance Ticker',
		name: 'binanceTicker',
		icon: { light: 'file:binance-ticker.svg', dark: 'file:binance-ticker.dark.svg' },
		group: ['input'],
		version: 1,
		subtitle: '={{$parameter["marketType"] === "spot" ? "Spot" : $parameter["marketType"] === "futures_usd_m" ? "USD-M Futures" : "COIN-M Futures"}}',
		description: 'Fetch current cryptocurrency prices from Binance Spot or Futures markets',
		defaults: {
			name: 'Binance Ticker',
		},
		inputs: [NodeConnectionTypes.Main],
		outputs: [NodeConnectionTypes.Main],
		credentials: [
			{
				name: 'binanceTickerApi',
				required: false,
			},
		],
		usableAsTool: true,
		properties: [
			{
				displayName: 'API Source',
				name: 'apiSource',
				type: 'options',
				options: [
					{
						name: 'Direct Binance',
						value: 'direct',
						description: 'Call Binance API directly using credentials or public endpoint',
					},
					{
						name: 'Custom URL',
						value: 'custom',
						description: 'Use a custom URL for proxy or testnet',
					},
				],
				default: 'direct',
				description: 'Choose how to fetch data from Binance',
			},
			{
				displayName: 'Custom URL',
				name: 'customUrl',
				type: 'string',
				default: '',
				placeholder: 'https://api.binance.com',
				description: 'Custom API base URL',
				displayOptions: {
					show: {
						apiSource: ['custom'],
					},
				},
			},
			{
				displayName: 'Market Type',
				name: 'marketType',
				type: 'options',
				options: [
					{
						name: 'Spot',
						value: 'spot',
						description: 'Spot market (api.binance.com)',
					},
					{
						name: 'USD-M Futures',
						value: 'futures_usd_m',
						description: 'USD-M Futures market (fapi.binance.com)',
					},
					{
						name: 'COIN-M Futures',
						value: 'futures_coin_m',
						description: 'COIN-M Futures market (dapi.binance.com)',
					},
				],
				default: 'spot',
				description: 'Choose spot or futures market',
			},
			{
				displayName: 'Price Type',
				name: 'priceType',
				type: 'options',
				options: [
					{
						name: 'Simple Price',
						value: 'simple',
						description: 'Latest price only (lighter response)',
					},
					{
						name: '24hr Statistics',
						value: 'stats_24h',
						description: 'Full 24hr statistics including price change, volume, high/low',
					},
				],
				default: 'simple',
				description: 'Type of price data to fetch',
			},
			{
				displayName: 'Symbol Source',
				name: 'symbolSource',
				type: 'options',
				options: [
					{
						name: 'Single Symbol',
						value: 'single',
						description: 'Fetch price for a single trading pair',
					},
					{
						name: 'Watchlist',
						value: 'watchlist',
						description: 'Fetch prices for multiple symbols defined in this node',
					},
					{
						name: 'Batch',
						value: 'batch',
						description: 'Fetch prices for multiple symbols at once',
					},
				],
				default: 'single',
				description: 'Choose how to specify symbols',
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
				displayName: 'Watchlist',
				name: 'watchlist',
				type: 'string',
				default: 'BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT',
				placeholder: 'BTCUSDT, ETHUSDT, SOLUSDT',
				description: 'Comma-separated list of trading pair symbols',
				displayOptions: {
					show: {
						symbolSource: ['watchlist'],
					},
				},
			},
			{
				displayName: 'Batch Symbols',
				name: 'batchSymbols',
				type: 'string',
				default: 'BTCUSDT, ETHUSDT',
				placeholder: 'BTCUSDT, ETHUSDT, SOLUSDT',
				description: 'Comma-separated list of trading pair symbols (max 100 for simple price)',
				displayOptions: {
					show: {
						symbolSource: ['batch'],
					},
				},
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		let credentials;
		try {
			credentials = await this.getCredentials('binanceTickerApi');
		} catch {
			credentials = {};
		}

		for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
			try {
				const apiSource = this.getNodeParameter('apiSource', itemIndex, 'direct') as string;
				const marketType = this.getNodeParameter('marketType', itemIndex, 'spot') as string;
				const priceType = this.getNodeParameter('priceType', itemIndex, 'simple') as string;
				const symbolSource = this.getNodeParameter('symbolSource', itemIndex, 'single') as string;

				let symbols: string[] = [];

				if (symbolSource === 'single') {
					const symbol = this.getNodeParameter('symbol', itemIndex, 'BTCUSDT') as string;
					symbols = [symbol.toUpperCase()];
				} else if (symbolSource === 'watchlist') {
					const watchlist = this.getNodeParameter(
						'watchlist',
						itemIndex,
						'BTCUSDT, ETHUSDT, BNBUSDT',
					) as string;
					symbols = watchlist
						.split(',')
						.map((s) => s.trim().toUpperCase())
						.filter((s) => s.length > 0);
				} else if (symbolSource === 'batch') {
					const batchSymbols = this.getNodeParameter(
						'batchSymbols',
						itemIndex,
						'BTCUSDT, ETHUSDT',
					) as string;
					symbols = batchSymbols
						.split(',')
						.map((s) => s.trim().toUpperCase())
						.filter((s) => s.length > 0);
				}

				if (symbols.length === 0) {
					throw new NodeOperationError(this.getNode(), 'No valid symbols provided', {
						itemIndex,
					});
				}

				const apiKey = (credentials?.apiKey as string) || '';

			const headers: Record<string, string> = {};
				if (apiKey) {
					headers['X-MBX-APIKEY'] = apiKey;
				}

				let baseUrl: string;
				let endpoint: string;

				if (marketType === 'spot') {
					baseUrl =
						apiSource === 'custom'
							? (this.getNodeParameter('customUrl', itemIndex) as string) ||
								'https://api.binance.com'
							: 'https://api.binance.com';
					endpoint = priceType === 'simple' ? '/api/v3/ticker/price' : '/api/v3/ticker/24hr';
				} else if (marketType === 'futures_usd_m') {
					baseUrl =
						apiSource === 'custom'
							? (this.getNodeParameter('customUrl', itemIndex) as string) ||
								'https://fapi.binance.com'
							: 'https://fapi.binance.com';
					endpoint = priceType === 'simple' ? '/fapi/v1/ticker/price' : '/fapi/v1/ticker/24hr';
				} else {
					baseUrl =
						apiSource === 'custom'
							? (this.getNodeParameter('customUrl', itemIndex) as string) ||
								'https://dapi.binance.com'
							: 'https://dapi.binance.com';
					endpoint = priceType === 'simple' ? '/dapi/v1/ticker/price' : '/dapi/v1/ticker/24hr';
				}

				const url = `${baseUrl}${endpoint}`;

				const fetchedAt = new Date().toISOString();

				if (priceType === 'simple') {
					const maxBatchSize = 100;
					if (symbols.length > maxBatchSize) {
						throw new NodeOperationError(
							this.getNode(),
							`Maximum ${maxBatchSize} symbols allowed for simple price endpoint`,
							{ itemIndex },
						);
					}

					if (symbols.length === 1) {
						const qs: Record<string, string> = { symbol: symbols[0] };

						const response = await this.helpers.httpRequest({
							method: 'GET' as IHttpRequestMethods,
							url,
							qs,
							headers,
							timeout: 30000,
						});

						const ticker = response as TickerPriceResponse;

						returnData.push({
							json: {
								symbol: ticker.symbol,
								marketType,
								priceType: 'simple',
								price: ticker.price,
								fetchedAt,
							},
							pairedItem: { item: itemIndex },
						});
					} else {
						const qs: Record<string, string> = {
							symbols: JSON.stringify(symbols),
						};

						const response = await this.helpers.httpRequest({
							method: 'GET' as IHttpRequestMethods,
							url,
							qs,
							headers,
							timeout: 30000,
						});

						const tickers = response as TickerPriceResponse[];

						const prices = tickers.map((ticker) => ({
							symbol: ticker.symbol,
							price: ticker.price,
						}));

						returnData.push({
							json: {
								prices,
								marketType,
								priceType: 'simple',
								count: prices.length,
								fetchedAt,
							},
							pairedItem: { item: itemIndex },
						});
					}
				} else {
					for (const symbol of symbols) {
						const qs: Record<string, string> = { symbol };

						const response = await this.helpers.httpRequest({
							method: 'GET' as IHttpRequestMethods,
							url,
							qs,
							headers,
							timeout: 30000,
						});

						const ticker = response as Ticker24hrResponse;

						returnData.push({
							json: {
								symbol: ticker.symbol,
								marketType,
								priceType: 'stats_24h',
								priceChange: ticker.priceChange,
								priceChangePercent: ticker.priceChangePercent,
								weightedAvgPrice: ticker.weightedAvgPrice,
								lastPrice: ticker.lastPrice,
								lastQty: ticker.lastQty,
								openPrice: ticker.openPrice,
								highPrice: ticker.highPrice,
								lowPrice: ticker.lowPrice,
								volume: ticker.volume,
								quoteVolume: ticker.quoteVolume,
								openTime: ticker.openTime,
								closeTime: ticker.closeTime,
								trades: ticker.count,
								fetchedAt,
							},
							pairedItem: { item: itemIndex },
						});
					}
				}
			} catch (error) {
				const errorObj = error as { message: string; context?: { itemIndex?: number } };
				if (this.continueOnFail()) {
					returnData.push({
						json: {
							error: errorObj.message,
						},
						pairedItem: { item: itemIndex },
					});
					continue;
				}

				if (errorObj.context) {
					errorObj.context.itemIndex = itemIndex;
					throw error;
				}

				throw new NodeOperationError(this.getNode(), errorObj.message, {
					itemIndex,
				});
			}
		}

		return [returnData];
	}
}
