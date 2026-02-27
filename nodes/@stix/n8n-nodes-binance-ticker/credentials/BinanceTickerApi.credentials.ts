/* eslint-disable @n8n/community-nodes/icon-validation */
import {
	IAuthenticateGeneric,
	ICredentialTestRequest,
	ICredentialType,
	INodeProperties,
	Icon,
} from 'n8n-workflow';

export class BinanceTickerApi implements ICredentialType {
	name = 'binanceTickerApi';

	displayName = 'Binance Ticker API';

	displayNamePlaceholder = 'Binance API Key';

	documentationUrl = 'https://binance-docs.github.io/apidocs/spot/en/#api-key-setup';

	icon: Icon = { light: 'file:icons/binance-ticker.svg', dark: 'file:icons/binance-ticker.dark.svg' };

	properties: INodeProperties[] = [
		{
			displayName: 'API Key',
			name: 'apiKey',
			type: 'string',
			default: '',
			typeOptions: { password: true },
			description: 'Binance API Key (optional for public endpoints)',
		},
		{
			displayName: 'API Secret',
			name: 'apiSecret',
			type: 'string',
			default: '',
			typeOptions: { password: true },
			description: 'Binance API Secret (optional for public endpoints)',
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
			url: 'https://api.binance.com/api/v3/ping',
			method: 'GET',
		},
	};
}
