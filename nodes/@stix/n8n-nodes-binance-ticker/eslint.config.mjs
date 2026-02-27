import withN8n from 'eslint-config-n8n/base';

export default [
	{
		ignores: ['dist/**/*', 'node_modules/**/*', '*.config.js'],
	},
	...withN8n,
];
