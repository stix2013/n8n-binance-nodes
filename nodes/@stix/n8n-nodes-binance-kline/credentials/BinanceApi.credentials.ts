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
      url: 'https://api.binance.com/api/v3/account',
      method: 'GET',
    },
  };
}
