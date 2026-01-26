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

interface BinanceApiKline {
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
	ignore: string;
}

interface PriceResponse {
	symbol: string;
	data: BinanceApiKline[];
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
		description: 'Fetch candlestick/kline data from Binance API',
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

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		// Get credentials
		const credentials = await this.getCredentials('binanceApi');

		for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
			try {
				const symbolSource = this.getNodeParameter('symbolSource', itemIndex, 'single') as string;
				const interval = this.getNodeParameter('interval', itemIndex, '1h') as string;
				const limit = this.getNodeParameter('limit', itemIndex, 50) as number;

				let symbols: string[] = [];

				if (symbolSource === 'watchlist') {
					// Get symbols from credentials watchlist
					const watchlist = (credentials.watchlist as string) || '';
					if (!watchlist || watchlist.trim() === '') {
						throw new NodeOperationError(
							this.getNode(),
							'Watchlist is empty. Please add symbols to your Binance API credentials watchlist.',
							{ itemIndex },
						);
					}
					// Parse comma-separated symbols and clean up
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

					// Debug: log symbols being fetched
					this.logger.debug(`Watchlist mode: Fetching data for ${symbols.length} symbols: ${symbols.join(', ')}`);
					// Parse comma-separated symbols and clean up
					symbols = watchlist
						.split(',')
						.map((s) => s.trim().toUpperCase())
						.filter((s) => s.length > 0);

					if (symbols.length === 0) {
						throw new NodeOperationError(
							this.getNode(),
							'No valid symbols found in watchlist.',
							{ itemIndex },
						);
					}
				} else {
					// Single symbol mode
					const symbol = this.getNodeParameter('symbol', itemIndex, 'BTCUSDT') as string;
					symbols = [symbol.toUpperCase()];
				}

				// Fetch kline data for each symbol
				for (const symbol of symbols) {
					const response = await this.helpers.httpRequest({
						method: 'GET' as IHttpRequestMethods,
						url: 'http://api:8000/api/binance/price',
						qs: {
							symbol,
							interval,
							limit,
						},
						timeout: 30000,
					});

					// Parse the kline data - API returns transformed data
					const priceResponse = response as PriceResponse;
					const klines: ParsedKline[] = priceResponse.data.map((k: BinanceApiKline) => ({
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

					// Get the latest kline for summary
					const latestKline = klines[klines.length - 1];

					returnData.push({
						json: {
							symbol,
							interval,
							limit,
							currentPrice: latestKline?.close || null,
							klineCount: klines.length,
							klines,
							fetchedAt: new Date().toISOString(),
						},
						pairedItem: { item: itemIndex },
					});
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
