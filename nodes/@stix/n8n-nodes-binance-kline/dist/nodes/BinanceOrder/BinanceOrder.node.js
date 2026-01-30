"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BinanceOrder = void 0;
const n8n_workflow_1 = require("n8n-workflow");
class BinanceOrder {
    constructor() {
        this.description = {
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
            inputs: [n8n_workflow_1.NodeConnectionTypes.Main],
            outputs: [n8n_workflow_1.NodeConnectionTypes.Main],
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
            ],
        };
    }
    async execute() {
        const items = this.getInputData();
        const returnData = [];
        for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
            try {
                const symbol = this.getNodeParameter('symbol', itemIndex);
                const side = this.getNodeParameter('side', itemIndex);
                const type = this.getNodeParameter('type', itemIndex);
                const quantity = this.getNodeParameter('quantity', itemIndex);
                const price = this.getNodeParameter('price', itemIndex, undefined);
                const stopPrice = this.getNodeParameter('stopPrice', itemIndex, undefined);
                const body = {
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
                const response = await this.helpers.httpRequest({
                    method: 'POST',
                    url: 'http://api:8000/api/binance/order',
                    body,
                    timeout: 30000,
                });
                returnData.push({
                    json: response,
                    pairedItem: { item: itemIndex },
                });
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
                throw new n8n_workflow_1.NodeOperationError(this.getNode(), error, {
                    itemIndex,
                });
            }
        }
        return [returnData];
    }
}
exports.BinanceOrder = BinanceOrder;
//# sourceMappingURL=BinanceOrder.node.js.map