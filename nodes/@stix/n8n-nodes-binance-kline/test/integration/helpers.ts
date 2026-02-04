import { IExecuteFunctions, INodeExecutionData, IDataObject } from 'n8n-workflow';
import { BinanceOrder } from '../../nodes/BinanceOrder/BinanceOrder.node';
import axios from 'axios';

export const executeBinanceOrderNode = async (
    nodeParameters: IDataObject,
    inputData: INodeExecutionData[] = [{ json: {} }]
) => {
    const node = new BinanceOrder();

    const context = {
        getInputData: () => inputData,
        getNodeParameter: (name: string, index: number, defaultValue?: any) => {
            // Handle specific parameter checks if needed
            if (name in nodeParameters) {
                return nodeParameters[name];
            }
            return defaultValue;
        },
        helpers: {
            httpRequest: jest.fn().mockImplementation(async (options) => {
                // Proxy the request to the real running FastAPI service
                try {
                    const response = await axios({
                        method: options.method,
                        url: options.url,
                        params: options.qs,
                        data: options.body,
                        headers: options.headers,
                        validateStatus: () => true // Let the node handle status codes
                    });
                    
                    if (response.status >= 400) {
                        // Mimic n8n's error behavior
                        const error: any = new Error(`Request failed with status code ${response.status}`);
                        error.statusCode = response.status;
                        error.body = response.data;
                        error.error = response.data; // n8n sometimes puts body in error
                        throw error;
                    }
                    
                    return response.data;
                } catch (error: any) {
                    throw error;
                }
            }),
        },
        continueOnFail: () => false,
        getNode: () => ({ name: 'BinanceOrder' }),
    } as unknown as IExecuteFunctions;

    // Execute the node
    return await node.execute.call(context);
};
