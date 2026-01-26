"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BinanceApi = void 0;
class BinanceApi {
    constructor() {
        this.name = 'binanceApi';
        this.displayName = 'Binance API';
        this.displayNamePlaceholder = 'Binance API Key';
        this.documentationUrl = 'https://docs.n8n.io/integrations/community-nodes/binance';
        this.icon = { light: 'file:icons/binance-kline.svg', dark: 'file:icons/binance-kline.dark.svg' };
        this.properties = [
            {
                displayName: 'API Key',
                name: 'apiKey',
                type: 'string',
                default: '',
                typeOptions: { password: true },
            },
            {
                displayName: 'API Secret',
                name: 'apiSecret',
                type: 'string',
                default: '',
                typeOptions: { password: true },
            },
            {
                displayName: 'Watchlist',
                name: 'watchlist',
                type: 'string',
                default: '',
                placeholder: 'BTCUSDT, ETHUSDT, SOLUSDT',
                description: 'Comma-separated list of your favorite crypto pairs for quick access',
            },
        ];
        this.authenticate = {
            type: 'generic',
            properties: {
                headers: {
                    'X-MBX-APIKEY': '={{$credentials.apiKey}}',
                },
            },
        };
        this.test = {
            request: {
                url: 'https://api.binance.com/api/v3/account',
                method: 'GET',
            },
        };
    }
}
exports.BinanceApi = BinanceApi;
//# sourceMappingURL=BinanceApi.credentials.js.map