"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChartCrypto = void 0;
const n8n_workflow_1 = require("n8n-workflow");
class ChartCrypto {
    constructor() {
        this.description = {
            displayName: 'Chart Crypto',
            name: 'chartCrypto',
            icon: { light: 'file:chart-crypto.svg', dark: 'file:chart-crypto.dark.svg' },
            group: ['input'],
            version: 1,
            description: 'Chart Crypto Node',
            defaults: {
                name: 'Chart Crypto',
            },
            inputs: [n8n_workflow_1.NodeConnectionTypes.Main],
            outputs: [n8n_workflow_1.NodeConnectionTypes.Main],
            usableAsTool: true,
            properties: [
                {
                    displayName: 'Symbol',
                    name: 'symbol',
                    type: 'string',
                    default: '',
                    placeholder: 'Placeholder value',
                    description: 'The description text',
                },
            ],
        };
    }
    async execute() {
        const items = this.getInputData();
        let item;
        let symbol;
        for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
            try {
                symbol = this.getNodeParameter('symbol', itemIndex, '');
                item = items[itemIndex];
                item.json.symbol = symbol;
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
exports.ChartCrypto = ChartCrypto;
//# sourceMappingURL=ChartCrypto.node.js.map