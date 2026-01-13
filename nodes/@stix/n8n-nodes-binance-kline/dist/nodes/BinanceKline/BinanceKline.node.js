"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BinanceKline = void 0;
const n8n_workflow_1 = require("n8n-workflow");
class BinanceKline {
    constructor() {
        this.description = {
            displayName: 'BinanceKline',
            name: 'binanceKline',
            icon: { light: 'file:binance-kline.svg', dark: 'file:binance-kline.dark.svg' },
            group: ['input'],
            version: 1,
            description: 'Binance Kline Node',
            defaults: {
                name: 'BinanceKline',
            },
            inputs: [n8n_workflow_1.NodeConnectionTypes.Main],
            outputs: [n8n_workflow_1.NodeConnectionTypes.Main],
            credentials: [
                {
                    name: 'binanceApi',
                    required: true,
                }
            ],
            usableAsTool: true,
            properties: [
                {
                    displayName: 'Symbol',
                    name: 'symbol',
                    type: 'string',
                    default: 'BTCUSDT',
                    placeholder: 'crypto pair',
                    description: 'The crypto pair',
                },
            ],
        };
    }
    async execute() {
        const items = this.getInputData();
        let item;
        let myString;
        for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
            try {
                myString = this.getNodeParameter('symbol', itemIndex, '');
                item = items[itemIndex];
                item.json.symbol = myString;
            }
            catch (error) {
                if (this.continueOnFail()) {
                    items.push({ json: this.getInputData(itemIndex)[0].json, error, pairedItem: itemIndex });
                }
                else {
                    if (error.context) {
                        error.context.itemIndex = itemIndex;
                        throw error;
                    }
                    throw new n8n_workflow_1.NodeOperationError(this.getNode(), error, {
                        itemIndex,
                    });
                }
            }
        }
        return [items];
    }
}
exports.BinanceKline = BinanceKline;
//# sourceMappingURL=BinanceKline.node.js.map