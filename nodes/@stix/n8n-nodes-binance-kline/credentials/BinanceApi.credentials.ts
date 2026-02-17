/* eslint-disable @n8n/community-nodes/icon-validation */
import {
  IAuthenticateGeneric,
  ICredentialTestRequest,
  ICredentialType,
  INodeProperties,
  Icon,
} from 'n8n-workflow';

export class BinanceApi implements ICredentialType {
  name = 'binanceApi';
  displayName = 'Binance API';
  displayNamePlaceholder = 'Binance API Key';
  documentationUrl = 'https://docs.n8n.io/integrations/community-nodes/binance';
  icon: Icon = { light: 'file:icons/binance-kline.svg', dark: 'file:icons/binance-kline.dark.svg' };
  properties: INodeProperties[] = [
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
    {
      displayName: 'Base URL',
      name: 'baseUrl',
      type: 'string',
      default: 'https://api.binance.com',
      placeholder: 'https://api.binance.com',
      description: 'Binance API base URL. Use for custom endpoints or proxies.',
    },
    {
      displayName: 'API Path',
      name: 'apiPath',
      type: 'string',
      default: '/api/v3/',
      placeholder: '/api/v3/',
      description: 'Binance API path prefix for spot market',
    },
    {
      displayName: 'Futures Base URL',
      name: 'futuresBaseUrl',
      type: 'string',
      default: 'https://fapi.binance.com',
      placeholder: 'https://fapi.binance.com',
      description: 'Binance USD-M Futures API base URL',
    },
    {
      displayName: 'Futures API Path',
      name: 'futuresApiPath',
      type: 'string',
      default: '/fapi/v1/',
      placeholder: '/fapi/v1/',
      description: 'Binance USD-M Futures API path prefix',
    },
  ];

  authenticate: IAuthenticateGeneric = {
    type: 'generic',
    properties: {
      headers: {
        'X-MBX-APIKEY': '={{$credentials.apiKey}}',
      },
    },
  };

  test: ICredentialTestRequest = {
    request: {
      url: '={{$credentials.baseUrl}}{{$credentials.apiPath}}ping',
      method: 'GET',
    },
  };
}
