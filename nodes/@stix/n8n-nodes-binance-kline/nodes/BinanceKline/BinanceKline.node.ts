import type {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	IHttpRequestMethods,
} from 'n8n-workflow';
import { NodeConnectionTypes, NodeOperationError } from 'n8n-workflow';

interface ParsedKline {
	openTime: number;
	open: string;
	high: string;
	low: string;
	close: string;
	volume: string;
	closeTime: number;
	quoteVolume: string;
	trades: number;
	takerBuyBaseVolume: string;
	takerBuyQuoteVolume: string;
}



interface ProxyPriceDataPoint {
	open_time: string;
	open_price: number;
	high_price: number;
	low_price: number;
	close_price: number;
	volume: number;
	close_time: string;
	quote_asset_volume: number;
	number_of_trades: number;
	taker_buy_base_asset_volume: number;
	taker_buy_quote_asset_volume: number;
	ignore?: string;
}

interface ProxyPriceResponse {
	symbol: string;
	data: ProxyPriceDataPoint[];
	count: number;
}

export class BinanceKline implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Binance Kline',
		name: 'binanceKline',
		icon: { light: 'file:binance-kline.svg', dark: 'file:binance-kline.dark.svg' },
		group: ['input'],
		version: 1,
		subtitle: '={{$parameter["symbolSource"] === "watchlist" ? "Watchlist" : $parameter["symbol"]}}',
		description: 'Fetch candlestick/kline data from Binance Spot or USD-M Futures API',
		defaults: {
			name: 'Binance Kline',
		},
		inputs: [NodeConnectionTypes.Main],
		outputs: [NodeConnectionTypes.Main],
		credentials: [
			{
				name: 'binanceApi',
				required: true,
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
						name: 'Proxy API',
						value: 'proxy',
						description: 'Use the FastAPI proxy (default: http://api:8000)',
					},
					{
						name: 'Direct Binance',
						value: 'direct',
						description: 'Call Binance API directly using credentials',
					},
					{
						name: 'Custom URL',
						value: 'custom',
						description: 'Use a custom URL',
					},
				],
				default: 'proxy',
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
				displayName: 'Custom Path',
				name: 'customPath',
				type: 'string',
				default: '/api/v3/klines',
				placeholder: '/api/v3/klines',
				description: 'Custom API endpoint path',
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
						value: 'futures',
						description: 'USD-M Futures market (fapi.binance.com)',
					},
				],
				default: 'spot',
				description: 'Choose spot or futures market',
			},
			{
				displayName: 'Futures Market Type',
				name: 'futuresMarketType',
				type: 'options',
				displayOptions: {
					show: {
						marketType: ['futures'],
						apiSource: ['proxy'],
					},
				},
				options: [
					{
						name: 'USD-M Futures',
						value: 'usd_m',
						description: 'USD-Margined Futures (fapi.binance.com)',
					},
					{
						name: 'COIN-M Futures',
						value: 'coin_m',
						description: 'COIN-Margined Futures (dapi.binance.com)',
					},
				],
				default: 'usd_m',
				description: 'Choose USD-M or COIN-M futures market',
			},
			{
				displayName: 'Futures Data Type',
				name: 'futuresDataType',
				type: 'options',
				displayOptions: {
					show: {
						marketType: ['futures'],
					},
				},
				options: [
					{
						name: 'Kline',
						value: 'kline',
						description: 'Standard futures candlestick data',
					},
					{
						name: 'Mark Price Kline',
						value: 'markPriceKline',
						description: 'Mark price candlestick data',
					},
					{
						name: 'Open Interest',
						value: 'openInterest',
						description: 'Current open interest for symbol',
					},
					{
						name: 'Open Interest History',
						value: 'openInterestHist',
						description: 'Historical open interest data',
					},
				],
				default: 'kline',
				description: 'Type of futures data to fetch',
			},
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
				displayOptions: {
					show: {
						marketType: ['spot'],
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
					{ name: '1 Week', value: '1w' },
					{ name: '12 Hours', value: '12h' },
					{ name: '15 Minutes', value: '15m' },
					{ name: '2 Hours', value: '2h' },
					{ name: '30 Minutes', value: '30m' },
					{ name: '4 Hours', value: '4h' },
					{ name: '5 Minutes', value: '5m' },
					{ name: '6 Hours', value: '6h' },
					{ name: '8 Hours', value: '8h' },
				],
				default: '1h',
				description: 'Kline/candlestick interval',
				displayOptions: {
					show: {
						marketType: ['futures'],
						futuresDataType: ['kline', 'markPriceKline', 'openInterestHist'],
					},
				},
			},
			{
				displayName: 'Limit',
				name: 'limit',
				type: 'number',
				typeOptions: {
					minValue: 1,
					maxValue: 1500,
				},
				default: 50,
				description: 'Max number of results to return',
				displayOptions: {
					show: {
						futuresDataType: ['kline', 'markPriceKline', 'openInterestHist'],
						marketType: ['futures'],
					},
				},
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
				displayOptions: {
					show: {
						marketType: ['spot'],
					},
				},
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		const credentials = await this.getCredentials('binanceApi');

		for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
			try {
				const apiSource = this.getNodeParameter('apiSource', itemIndex, 'proxy') as string;
				const marketType = this.getNodeParameter('marketType', itemIndex, 'spot') as string;
				const symbolSource = this.getNodeParameter('symbolSource', itemIndex, 'single') as string;
				const limit = this.getNodeParameter('limit', itemIndex, 50) as number;

				let symbols: string[] = [];

				if (symbolSource === 'watchlist') {
					const watchlist = (credentials.watchlist as string) || '';
					if (!watchlist || watchlist.trim() === '') {
						throw new NodeOperationError(
							this.getNode(),
							'Watchlist is empty. Please add symbols to your Binance API credentials watchlist.',
							{ itemIndex },
						);
					}
					symbols = watchlist
						.split(',')
						.map((s) => s.trim().toUpperCase())
						.filter((s) => s.length > 0);

					if (symbols.length === 0) {
						throw new NodeOperationError(
							this.getNode(),
							'No valid symbols found in watchlist. Please check your watchlist format (e.g., BTCUSDT, ETHUSDT, SOLUSDT).',
							{ itemIndex },
						);
					}
				} else {
					const symbol = this.getNodeParameter('symbol', itemIndex, 'BTCUSDT') as string;
					symbols = [symbol.toUpperCase()];
				}

				for (const symbol of symbols) {
					let url: string;
					const qs: Record<string, string | number> = { symbol };
					let dataType = 'kline';

					if (marketType === 'futures') {
						dataType = this.getNodeParameter('futuresDataType', itemIndex, 'kline') as string;
						const interval = this.getNodeParameter('interval', itemIndex, '1h') as string;
						// Get market type (usd_m or coin_m) - default to usd_m for proxy
						const futuresMarketType = this.getNodeParameter('futuresMarketType', itemIndex, 'usd_m') as string;

						if (apiSource === 'proxy') {
							const proxyBaseUrl = 'http://api:8000';
							url = `${proxyBaseUrl}/api/binance/futures/${dataType}`;
							qs.market_type = futuresMarketType;
							if (dataType !== 'openInterest') {
								qs.interval = interval;
								qs.limit = limit;
							}
						} else if (apiSource === 'custom') {
							const customUrl = this.getNodeParameter('customUrl', itemIndex) as string;
							const customPath = this.getNodeParameter('customPath', itemIndex) as string;
							url = `${customUrl}${customPath}`;
							if (dataType !== 'openInterest') {
								qs.interval = interval;
								qs.limit = limit;
							}
						} else {
							const baseUrl = (credentials.futuresBaseUrl as string) || 'https://fapi.binance.com';
							const apiPath = (credentials.futuresApiPath as string) || '/fapi/v1/';

							if (dataType === 'kline') {
								url = `${baseUrl}${apiPath}klines`;
								qs.interval = interval;
								qs.limit = limit;
							} else if (dataType === 'markPriceKline') {
								url = `${baseUrl}${apiPath}markPriceKlines`;
								qs.interval = interval;
								qs.limit = limit;
							} else if (dataType === 'openInterest') {
								url = `${baseUrl}${apiPath}openInterest`;
							} else if (dataType === 'openInterestHist') {
								url = `${baseUrl}/futures/data/openInterestHist`;
								qs.period = interval;
								qs.limit = limit;
							} else {
								url = `${baseUrl}${apiPath}klines`;
								qs.interval = interval;
								qs.limit = limit;
							}
						}
					} else {
						const interval = this.getNodeParameter('interval', itemIndex, '1h') as string;

						if (apiSource === 'proxy') {
							const proxyBaseUrl = 'http://api:8000';
							url = `${proxyBaseUrl}/api/binance/price`;
							qs.interval = interval;
							qs.limit = limit;
						} else if (apiSource === 'custom') {
							const customUrl = this.getNodeParameter('customUrl', itemIndex) as string;
							const customPath = this.getNodeParameter('customPath', itemIndex) as string;
							url = `${customUrl}${customPath}`;
							qs.interval = interval;
							qs.limit = limit;
						} else {
							const baseUrl = (credentials.baseUrl as string) || 'https://api.binance.com';
							const apiPath = (credentials.apiPath as string) || '/api/v3/';
							url = `${baseUrl}${apiPath}klines`;
							qs.interval = interval;
							qs.limit = limit;
						}
					}

					const response = await this.helpers.httpRequestWithAuthentication.call(
						this,
						'binanceApi',
						{
							method: 'GET' as IHttpRequestMethods,
							url,
							qs,
							timeout: 30000,
						},
					);

					if (marketType === 'futures' && dataType === 'openInterest') {
						const oi = response as { symbol: string; openInterest: string; time: number };
						returnData.push({
							json: {
								symbol,
								marketType,
								dataType,
								openInterest: oi.openInterest,
								time: oi.time,
								fetchedAt: new Date().toISOString(),
							},
							pairedItem: { item: itemIndex },
						});
					} else if (marketType === 'futures' && dataType === 'openInterestHist') {
						const oiHist = response as Array<{ symbol: string; openInterest: string; timestamp: number }>;
						returnData.push({
							json: {
								symbol,
								marketType,
								dataType,
								openInterestHistory: oiHist,
								count: oiHist.length,
								fetchedAt: new Date().toISOString(),
							},
							pairedItem: { item: itemIndex },
						});
					} else {
						let klines: ParsedKline[];

						if (apiSource === 'proxy' && marketType === 'spot') {
							// Proxy spot response format: {symbol, data: [{open_time, open_price, ...}]}
							const priceResponse = response as ProxyPriceResponse;
							klines = priceResponse.data.map((k) => ({
								openTime: new Date(k.open_time).getTime(),
								open: String(k.open_price),
								high: String(k.high_price),
								low: String(k.low_price),
								close: String(k.close_price),
								volume: String(k.volume),
								closeTime: new Date(k.close_time).getTime(),
								quoteVolume: String(k.quote_asset_volume),
								trades: k.number_of_trades,
								takerBuyBaseVolume: String(k.taker_buy_base_asset_volume),
								takerBuyQuoteVolume: String(k.taker_buy_quote_asset_volume),
							}));
						} else if (apiSource === 'proxy' && marketType === 'futures' && dataType === 'kline') {
							// Proxy futures response format: {success, symbol, market_type, interval, data: [{open_time, ...}], count}
							const candleResponse = response as { data: Array<{
								open_time: string;
								open_price: number;
								high_price: number;
								low_price: number;
								close_price: number;
								volume: number;
								close_time: string;
								quote_volume: number;
								trades: number;
								taker_buy_base_volume: number;
								taker_buy_quote_volume: number;
							}> };
							klines = candleResponse.data.map((k) => ({
								openTime: new Date(k.open_time).getTime(),
								open: String(k.open_price),
								high: String(k.high_price),
								low: String(k.low_price),
								close: String(k.close_price),
								volume: String(k.volume),
								closeTime: new Date(k.close_time).getTime(),
								quoteVolume: String(k.quote_volume),
								trades: k.trades,
								takerBuyBaseVolume: String(k.taker_buy_base_volume),
								takerBuyQuoteVolume: String(k.taker_buy_quote_volume),
							}));
						} else {
							// Direct Binance API response format: [[openTime, open, high, low, close, volume, closeTime, ...]]
							const rawKlines = response as unknown[][];
							klines = rawKlines.map((k: unknown[]) => ({
								openTime: Number(k[0]),
								open: String(k[1]),
								high: String(k[2]),
								low: String(k[3]),
								close: String(k[4]),
								volume: String(k[5]),
								closeTime: Number(k[6]),
								quoteVolume: String(k[7]),
								trades: Number(k[8]),
								takerBuyBaseVolume: String(k[9]),
								takerBuyQuoteVolume: String(k[10]),
							}));
						}

						const latestKline = klines[klines.length - 1];

						returnData.push({
							json: {
								symbol,
								marketType,
								dataType: marketType === 'futures' ? dataType : 'kline',
								interval: qs.interval || null,
								limit,
								currentPrice: latestKline?.close || null,
								klineCount: klines.length,
								klines,
								fetchedAt: new Date().toISOString(),
							},
							pairedItem: { item: itemIndex },
						});
					}
				}
			} catch (error) {
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

				throw new NodeOperationError(this.getNode(), error, {
					itemIndex,
				});
			}
		}

		return [returnData];
	}
}