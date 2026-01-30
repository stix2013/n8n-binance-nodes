import type {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	IHttpRequestMethods,
} from 'n8n-workflow';
import { NodeConnectionTypes, NodeOperationError } from 'n8n-workflow';

export class BinanceOrder implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Binance Order',
		name: 'binanceOrder',
		icon: { light: 'file:../../icons/binance-kline.svg', dark: 'file:../../icons/binance-kline.dark.svg' },
		group: ['transform'],
		version: 1,
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
					{ name: 'Market', value: 'MARKET' },
					{ name: 'Stop Loss', value: 'STOP_LOSS' },
					{ name: 'Stop Loss Limit', value: 'STOP_LOSS_LIMIT' },
					{ name: 'Take Profit', value: 'TAKE_PROFIT' },
					{ name: 'Take Profit Limit', value: 'TAKE_PROFIT_LIMIT' },
					{ name: 'Limit Maker', value: 'LIMIT_MAKER' },
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

		for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
			try {
				const symbol = this.getNodeParameter('symbol', itemIndex) as string;
				const side = this.getNodeParameter('side', itemIndex) as string;
				const type = this.getNodeParameter('type', itemIndex) as string;
				const quantity = this.getNodeParameter('quantity', itemIndex) as number;
				const price = this.getNodeParameter('price', itemIndex, undefined) as number | undefined;
				const stopPrice = this.getNodeParameter('stopPrice', itemIndex, undefined) as number | undefined;
				
				// Bracket params
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

				const body: any = {
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

				const response = await this.helpers.httpRequest({
					method: 'POST' as IHttpRequestMethods,
					url: 'http://api:8000/api/binance/order',
					body,
					timeout: 30000,
				});

				returnData.push({
					json: response as any,
					pairedItem: { item: itemIndex },
				});
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
