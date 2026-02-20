import {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	NodeApiError,
	NodeOperationError,
} from 'n8n-workflow';

export class BinanceKlineIndicators implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Binance Kline Indicators',
		name: 'binanceKlineIndicators',
		icon: 'file:binance-kline-indicators.svg',
		group: ['transform'],
		version: 1,
		description: 'Compile technical indicators (RSI, MACD, SMA, EMA) from Binance Kline data via API',
		defaults: {
			name: 'Binance Kline Indicators',
		},
		inputs: ['main'],
		outputs: ['main'],
		credentials: [], // No credentials required for this node as it POSTs to our API
		properties: [
			{
				displayName: 'API URL',
				name: 'apiUrl',
				type: 'string',
				default: 'http://api:8000/api/ingest/analyze',
				description: 'The URL of the API endpoint to POST the data to',
				required: true,
			},
			{
				displayName: 'Parameters',
				name: 'parameters',
				type: 'collection',
				placeholder: 'Add Parameter',
				default: {},
				options: [
					{
						displayName: 'RSI Period',
						name: 'rsi_period',
						type: 'number',
						default: 14,
						typeOptions: {
							minValue: 2,
						},
						description: 'Relative Strength Index calculation period',
					},
					{
						displayName: 'MACD Fast Period',
						name: 'macd_fast',
						type: 'number',
						default: 12,
						typeOptions: {
							minValue: 2,
						},
						description: 'Fast EMA period for MACD',
					},
					{
						displayName: 'MACD Slow Period',
						name: 'macd_slow',
						type: 'number',
						default: 26,
						typeOptions: {
							minValue: 2,
						},
						description: 'Slow EMA period for MACD',
					},
					{
						displayName: 'MACD Signal Period',
						name: 'macd_signal',
						type: 'number',
						default: 9,
						typeOptions: {
							minValue: 2,
						},
						description: 'Signal line EMA period for MACD',
					},
					{
						displayName: 'SMA Enabled',
						name: 'sma_enabled',
						type: 'boolean',
						default: true,
						description: 'Whether to calculate Simple Moving Averages',
					},
					{
						displayName: 'EMA Enabled',
						name: 'ema_enabled',
						type: 'boolean',
						default: true,
						description: 'Whether to calculate Exponential Moving Averages',
					},
				],
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		for (let i = 0; i < items.length; i++) {
			try {
				const apiUrl = this.getNodeParameter('apiUrl', i) as string;
				const parameters = this.getNodeParameter('parameters', i) as any;
				
				// The incoming item from BinanceKline node
				const itemData = items[i].json;

				// Construct the payload to match the IngestRequest model
				const body = {
					data: itemData,
					parameters: {
						rsi_period: parameters.rsi_period !== undefined ? parameters.rsi_period : 14,
						macd_fast: parameters.macd_fast !== undefined ? parameters.macd_fast : 12,
						macd_slow: parameters.macd_slow !== undefined ? parameters.macd_slow : 26,
						macd_signal: parameters.macd_signal !== undefined ? parameters.macd_signal : 9,
						sma_enabled: parameters.sma_enabled !== undefined ? parameters.sma_enabled : true,
						ema_enabled: parameters.ema_enabled !== undefined ? parameters.ema_enabled : true,
					},
				};

				// Execute the HTTP Request
				const responseData = await this.helpers.httpRequest({
					method: 'POST',
					url: apiUrl,
					body: body,
					json: true,
				});

				returnData.push({
					json: responseData,
				});
			} catch (error) {
				if (this.continueOnFail()) {
					returnData.push({ json: { error: error.message } });
					continue;
				}
				
				if (error.statusCode) {
					throw new NodeApiError(this.getNode(), error as any, { itemIndex: i });
				}
				
				throw new NodeOperationError(this.getNode(), error, { itemIndex: i });
			}
		}

		return [returnData];
	}
}
