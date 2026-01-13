import {
  IAuthenticateGeneric,
  ICredentialTestRequest,
  ICredentialType,
  INodeProperties,
} from 'n8n-workflow';

export class BinanceApi implements ICredentialType {
  name = 'binanceApi';
  displayName = 'Binance API';
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
    },
  ];

  authenticate: IAuthenticateGeneric = {
    type: 'generic',
    properties: {
      headers: {
        Authorization: 'Bearer {{binanceApi.apiKey}}',
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
