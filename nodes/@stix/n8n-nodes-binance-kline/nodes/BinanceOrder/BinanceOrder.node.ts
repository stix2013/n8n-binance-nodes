import type {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	IHttpRequestMethods,
	IDataObject,
} from 'n8n-workflow';
import { NodeConnectionTypes, NodeOperationError } from 'n8n-workflow';
import { createHmac } from 'crypto';

export class BinanceOrder implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Binance Order',
		name: 'binanceOrder',
		icon: { light: 'file:../../icons/binance-kline.svg', dark: 'file:../../icons/binance-kline.dark.svg' },
		group: ['transform'],
		version: 1,
		usableAsTool: true,
		subtitle: '={{$parameter["side"]}} {{$parameter["symbol"]}}',
		description: 'Place an order on Binance API',
		defaults: {
			name: 'Binance Order',
		},
		inputs: [NodeConnectionTypes.Main],
		outputs: [NodeConnectionTypes.Main],
		credentials: [
			{
				name: 'binanceApi',
				required: true,
			},
		],
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
						description: 'Call Binance API directly with HMAC signing',
					},
					{
						name: 'Custom URL',
						value: 'custom',
						description: 'Use a custom URL',
					},
				],
				default: 'proxy',
				description: 'Choose how to place orders on Binance',
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
				default: '/api/v3/order',
				placeholder: '/api/v3/order',
				description: 'Custom API endpoint path',
				displayOptions: {
					show: {
						apiSource: ['custom'],
					},
				},
			},
			{
				displayName: 'Symbol',
				name: 'symbol',
				type: 'string',
				default: 'BTCUSDT',
				placeholder: 'e.g. BTCUSDT, ETHUSDT',
				description: 'The trading pair symbol',
				required: true,
			},
			{
				displayName: 'Side',
				name: 'side',
				type: 'options',
				options: [
					{ name: 'Buy', value: 'BUY' },
					{ name: 'Sell', value: 'SELL' },
				],
				default: 'BUY',
				description: 'Whether to buy or sell',
				required: true,
			},
			{
				displayName: 'Type',
				name: 'type',
				type: 'options',
				options: [
					{ name: 'Limit', value: 'LIMIT' },
					{ name: 'Limit Maker', value: 'LIMIT_MAKER' },
					{ name: 'Market', value: 'MARKET' },
					{ name: 'Stop Loss', value: 'STOP_LOSS' },
					{ name: 'Stop Loss Limit', value: 'STOP_LOSS_LIMIT' },
					{ name: 'Take Profit', value: 'TAKE_PROFIT' },
					{ name: 'Take Profit Limit', value: 'TAKE_PROFIT_LIMIT' },
				],
				default: 'MARKET',
				description: 'The type of order to place',
				required: true,
			},
			{
				displayName: 'Quantity',
				name: 'quantity',
				type: 'number',
				default: 0,
				description: 'The quantity to buy/sell',
				required: true,
			},
			{
				displayName: 'Price',
				name: 'price',
				type: 'number',
				default: 0,
				description: 'The price for LIMIT orders',
				displayOptions: {
					show: {
						type: ['LIMIT', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT', 'LIMIT_MAKER'],
					},
				},
			},
			{
				displayName: 'Stop Price',
				name: 'stopPrice',
				type: 'number',
				default: 0,
				description: 'The stop price for STOP orders',
				displayOptions: {
					show: {
						type: ['STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT'],
					},
				},
			},
			{
				displayName: 'Bracket Order (SL/TP)',
				name: 'useBracket',
				type: 'boolean',
				default: false,
				description: 'Whether to add Take Profit and Stop Loss orders',
				displayOptions: {
					show: {
						type: ['LIMIT', 'MARKET'],
					},
				},
			},
			{
				displayName: 'Take Profit Price',
				name: 'takeProfitPrice',
				type: 'number',
				default: 0,
				required: true,
				displayOptions: {
					show: {
						useBracket: [true],
					},
				},
				description: 'Price to take profit',
			},
			{
				displayName: 'Stop Loss Price',
				name: 'stopLossPrice',
				type: 'number',
				default: 0,
				required: true,
				displayOptions: {
					show: {
						useBracket: [true],
					},
				},
				description: 'Trigger price for stop loss',
			},
			{
				displayName: 'Stop Loss Type',
				name: 'stopLossType',
				type: 'options',
				options: [
					{ name: 'Market', value: 'MARKET' },
					{ name: 'Limit', value: 'LIMIT' },
				],
				default: 'MARKET',
				displayOptions: {
					show: {
						useBracket: [true],
					},
				},
				description: 'Whether to execute Stop Loss at Market or Limit price',
			},
			{
				displayName: 'Stop Loss Limit Price',
				name: 'stopLossLimitPrice',
				type: 'number',
				default: 0,
				displayOptions: {
					show: {
						useBracket: [true],
						stopLossType: ['LIMIT'],
					},
				},
				description: 'Execution price for Stop Loss Limit order',
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		const credentials = await this.getCredentials('binanceApi');
		const apiKey = credentials.apiKey as string;
		const apiSecret = credentials.apiSecret as string;

		for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
			try {
				const apiSource = this.getNodeParameter('apiSource', itemIndex, 'proxy') as string;
				const symbol = this.getNodeParameter('symbol', itemIndex) as string;
				const side = this.getNodeParameter('side', itemIndex) as string;
				const type = this.getNodeParameter('type', itemIndex) as string;
				const quantity = this.getNodeParameter('quantity', itemIndex) as number;
				const price = this.getNodeParameter('price', itemIndex, 0) as number;
				const stopPrice = this.getNodeParameter('stopPrice', itemIndex, 0) as number;
				
				const useBracket = this.getNodeParameter('useBracket', itemIndex, false) as boolean;
				let takeProfitPrice: number | undefined;
				let stopLossPrice: number | undefined;
				let stopLossType: string | undefined;
				let stopLossLimitPrice: number | undefined;

				if (useBracket) {
					takeProfitPrice = this.getNodeParameter('takeProfitPrice', itemIndex) as number;
					stopLossPrice = this.getNodeParameter('stopLossPrice', itemIndex) as number;
					stopLossType = this.getNodeParameter('stopLossType', itemIndex) as string;
					if (stopLossType === 'LIMIT') {
						stopLossLimitPrice = this.getNodeParameter('stopLossLimitPrice', itemIndex) as number;
					}
				}

				if (apiSource === 'proxy') {
					const proxyBaseUrl = 'http://api:8000';
					const url = `${proxyBaseUrl}/api/binance/order`;
					
					const body: Record<string, unknown> = {
						symbol: symbol.toUpperCase(),
						side,
						type,
						quantity,
					};

					if (price !== undefined && price !== 0) {
						body.price = price;
					}

					if (stopPrice !== undefined && stopPrice !== 0) {
						body.stopPrice = stopPrice;
					}
					
					if (useBracket) {
						if (takeProfitPrice) body.takeProfitPrice = takeProfitPrice;
						if (stopLossPrice) body.stopLossPrice = stopLossPrice;
						if (stopLossType) body.stopLossType = stopLossType;
						if (stopLossLimitPrice) body.stopLossLimitPrice = stopLossLimitPrice;
					}

					const response = await this.helpers.httpRequestWithAuthentication.call(
						this,
						'binanceApi',
						{
							method: 'POST' as IHttpRequestMethods,
							url,
							body,
							timeout: 30000,
						},
					);

					returnData.push({
						json: response as IDataObject,
						pairedItem: { item: itemIndex },
					});
				} else if (apiSource === 'custom') {
					const customUrl = this.getNodeParameter('customUrl', itemIndex) as string;
					const customPath = this.getNodeParameter('customPath', itemIndex) as string;
					const url = `${customUrl}${customPath}`;
					
					const body: Record<string, unknown> = {
						symbol: symbol.toUpperCase(),
						side,
						type,
						quantity,
					};

					if (price !== 0) body.price = price;
					if (stopPrice !== 0) body.stopPrice = stopPrice;
					
					if (useBracket) {
						if (takeProfitPrice) body.takeProfitPrice = takeProfitPrice;
						if (stopLossPrice) body.stopLossPrice = stopLossPrice;
						if (stopLossType) body.stopLossType = stopLossType;
						if (stopLossLimitPrice) body.stopLossLimitPrice = stopLossLimitPrice;
					}

					const response = await this.helpers.httpRequestWithAuthentication.call(
						this,
						'binanceApi',
						{
							method: 'POST' as IHttpRequestMethods,
							url,
							body,
							timeout: 30000,
						},
					);

					returnData.push({
						json: response as IDataObject,
						pairedItem: { item: itemIndex },
					});
				} else {
					// Direct Binance API with HMAC signing
					const timestamp = Date.now();
					
					const params = new URLSearchParams();
					params.append('symbol', symbol.toUpperCase());
					params.append('side', side);
					params.append('type', type);
					params.append('quantity', quantity.toString());
					params.append('timestamp', timestamp.toString());

					if (price !== 0) {
						params.append('price', price.toString());
					}
					
					if (stopPrice !== 0) {
						params.append('stopPrice', stopPrice.toString());
					}

					const queryString = params.toString();
					const signature = createHmac('sha256', apiSecret)
						.update(queryString)
						.digest('hex');

					const baseUrl = (credentials.baseUrl as string) || 'https://api.binance.com';
					const apiPath = (credentials.apiPath as string) || '/api/v3/';
					const url = `${baseUrl}${apiPath}order`;

					const response = await this.helpers.httpRequest({
						method: 'POST' as IHttpRequestMethods,
						url,
						body: `${queryString}&signature=${signature}`,
						headers: {
							'Content-Type': 'application/x-www-form-urlencoded',
							'X-MBX-APIKEY': apiKey,
						},
						timeout: 30000,
					});

					returnData.push({
						json: response as IDataObject,
						pairedItem: { item: itemIndex },
					});

					// Handle bracket orders (OCO) for direct Binance
					if (useBracket && takeProfitPrice && stopLossPrice) {
						const ocoTimestamp = Date.now();
						const ocoParams = new URLSearchParams();
						ocoParams.append('symbol', symbol.toUpperCase());
						ocoParams.append('side', side === 'BUY' ? 'SELL' : 'BUY');
						ocoParams.append('quantity', quantity.toString());
						ocoParams.append('price', takeProfitPrice.toString());
						ocoParams.append('stopPrice', stopLossPrice.toString());
						ocoParams.append('stopLimitPrice', stopLossLimitPrice ? stopLossLimitPrice.toString() : stopLossPrice.toString());
						ocoParams.append('stopLimitTimeInForce', 'GTE_GTC');
						ocoParams.append('timestamp', ocoTimestamp.toString());

						const ocoQueryString = ocoParams.toString();
						const ocoSignature = createHmac('sha256', apiSecret)
							.update(ocoQueryString)
							.digest('hex');

						const ocoUrl = `${baseUrl}${apiPath}order/oco`;

						const ocoResponse = await this.helpers.httpRequest({
							method: 'POST' as IHttpRequestMethods,
							url: ocoUrl,
							body: `${ocoQueryString}&signature=${ocoSignature}`,
							headers: {
								'Content-Type': 'application/x-www-form-urlencoded',
								'X-MBX-APIKEY': apiKey,
							},
							timeout: 30000,
						});

						returnData.push({
							json: {
								ocoOrder: ocoResponse as Record<string, unknown>,
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

				throw new NodeOperationError(this.getNode(), error, {
					itemIndex,
				});
			}
		}

		return [returnData];
	}
}