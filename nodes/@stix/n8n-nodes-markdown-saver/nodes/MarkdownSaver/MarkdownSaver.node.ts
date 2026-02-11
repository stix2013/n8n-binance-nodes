import type {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
} from 'n8n-workflow';

/**
 * Apply template with variable substitution
 */
function applyTemplate(template: string, data: unknown): string {
	let result = template;

	// Replace {{ $json.key }} or {{ $json['key'] }} patterns
	const regex = /\{\{\s*\$json\.?(\w+|\['[^']+'\]|\["[^"]+"\])\s*\}\}/g;
	result = result.replace(regex, (match, key) => {
		// Clean up key (remove brackets and quotes if present)
		const cleanKey = key.replace(/^\['|'$\]|^\["|"$\]/g, '');
		const value = getNestedValue(data, cleanKey);
		return value !== undefined ? String(value) : match;
	});

	return result;
}

/**
 * Get nested value from object using dot notation
 */
function getNestedValue(obj: unknown, path: string): unknown {
	const keys = path.split('.');
	let value: unknown = obj;
	for (const key of keys) {
		if (value === null || value === undefined) {
			return undefined;
		}
		if (typeof value !== 'object') {
			return undefined;
		}
		value = (value as Record<string, unknown>)[key];
	}
	return value;
}

/**
 * Check if data can be formatted as a table
 */
function isTabularData(data: unknown[]): boolean {
	if (data.length === 0) return false;
	const firstItem = data[0];
	if (typeof firstItem !== 'object' || firstItem === null) return false;

	// Check if all items are objects with similar structure
	const keys = Object.keys(firstItem);
	return keys.length > 0 && data.every(item =>
		typeof item === 'object' &&
		item !== null &&
		Object.keys(item).length === keys.length
	);
}

/**
 * Convert array to markdown table
 */
function convertToTable(data: Record<string, unknown>[], includeHeaders: boolean): string {
	if (data.length === 0) return '';

	const keys = Object.keys(data[0]);
	let markdown = '';

	if (includeHeaders) {
		// Header row
		markdown += '| ' + keys.join(' | ') + ' |\n';
		// Separator row
		markdown += '|' + keys.map(() => ' --- ').join('|') + '|\n';
	}

	// Data rows
	for (const item of data) {
		const values = keys.map(key => {
			const value = item[key];
			if (value === null || value === undefined) return '';
			if (typeof value === 'object') return JSON.stringify(value);
			return String(value).replace(/\|/g, '\\|').replace(/\n/g, ' ');
		});
		markdown += '| ' + values.join(' | ') + ' |\n';
	}

	return markdown;
}

/**
 * Convert object to list item string
 */
function convertObjectToListItem(obj: Record<string, unknown>): string {
	const pairs: string[] = [];
	for (const [key, value] of Object.entries(obj)) {
		if (value !== null && value !== undefined) {
			if (typeof value === 'object') {
				pairs.push(`${key}: ${JSON.stringify(value)}`);
			} else {
				pairs.push(`${key}: ${value}`);
			}
		}
	}
	return pairs.join(', ');
}

/**
 * Convert array to markdown list
 */
function convertToList(data: unknown[]): string {
	let markdown = '';
	for (const item of data) {
		if (typeof item === 'object' && item !== null) {
			markdown += '- ' + convertObjectToListItem(item as Record<string, unknown>) + '\n';
		} else {
			markdown += '- ' + String(item) + '\n';
		}
	}
	return markdown;
}

/**
 * Convert object to markdown (key-value format)
 */
function convertObjectToMarkdown(obj: Record<string, unknown>): string {
	let markdown = '';
	for (const [key, value] of Object.entries(obj)) {
		if (value !== null && value !== undefined) {
			markdown += `## ${key}\n\n`;
			if (typeof value === 'object') {
				if (Array.isArray(value)) {
					markdown += convertToList(value) + '\n';
				} else {
					markdown += '```json\n' + JSON.stringify(value, null, 2) + '\n```\n\n';
				}
			} else {
				markdown += String(value) + '\n\n';
			}
		}
	}
	return markdown;
}

/**
 * Automatically convert JSON to markdown
 */
function autoConvertToMarkdown(data: unknown, format: string, includeHeaders: boolean): string {
	if (format === 'codeblock') {
		return '```json\n' + JSON.stringify(data, null, 2) + '\n```';
	}

	if (Array.isArray(data)) {
		if (data.length === 0) {
			return '*No data*';
		}

		if (format === 'table' || (format === 'auto' && isTabularData(data))) {
			return convertToTable(data as Record<string, unknown>[], includeHeaders);
		} else {
			return convertToList(data);
		}
	}

	if (typeof data === 'object' && data !== null) {
		return convertObjectToMarkdown(data as Record<string, unknown>);
	}

	return String(data);
}

/**
 * Escape markdown special characters
 */
function escapeMarkdownCharacters(content: string): string {
	// Escape characters that have special meaning in markdown
	return content
		.replace(/\\/g, '\\\\')  // Backslash
		.replace(/`/g, '\\`')   // Backtick
		.replace(/\*/g, '\\*')   // Asterisk
		.replace(/_/g, '\\_')    // Underscore
		.replace(/\{/g, '\\{')   // Curly braces
		.replace(/\}/g, '\\}')
		.replace(/\[/g, '\\[')   // Square brackets
		.replace(/\]/g, '\\]')
		.replace(/\(/g, '\\(')   // Parentheses
		.replace(/\)/g, '\\)')
		.replace(/#/g, '\\#')    // Hash
		.replace(/\+/g, '\\+')   // Plus
		.replace(/-/g, '\\-')    // Minus
		.replace(/\./g, '\\.')   // Dot
		.replace(/!/g, '\\!');   // Exclamation
}

/**
 * Apply character filtering to markdown content
 */
function applyCharacterFiltering(content: string, filtering: {
	removeNewlines?: boolean;
	removeCarriageReturns?: boolean;
	unescapeQuotes?: boolean;
	unescapeSingleQuotes?: boolean;
	escapeMarkdown?: boolean;
	customReplacements?: {
		replacements?: Array<{ find: string; replace: string }>;
	};
}): string {
	let result = content;

	// Unescape single quotes first (to avoid double escaping)
	if (filtering.unescapeSingleQuotes) {
		result = result.replace(/\\'/g, "'");
	}

	// Unescape double quotes
	if (filtering.unescapeQuotes) {
		result = result.replace(/\\"/g, '"');
	}

	// Remove carriage returns
	if (filtering.removeCarriageReturns) {
		result = result.replace(/\\r/g, '');
	}

	// Remove newlines
	if (filtering.removeNewlines) {
		result = result.replace(/\\n/g, ' ');
	}

	// Escape markdown special characters
	if (filtering.escapeMarkdown) {
		result = escapeMarkdownCharacters(result);
	}

	// Apply custom replacements
	if (filtering.customReplacements?.replacements) {
		for (const replacement of filtering.customReplacements.replacements) {
			if (replacement.find) {
				// Handle escaped characters in the find pattern
				const findPattern = replacement.find
					.replace(/\\n/g, '\n')
					.replace(/\\r/g, '\r')
					.replace(/\\t/g, '\t')
					.replace(/\\"/g, '"')
					.replace(/\\'/g, "'")
					.replace(/\\\\/g, '\\');
				result = result.split(findPattern).join(replacement.replace);
			}
		}
	}

	return result;
}

export class MarkdownSaver implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Markdown Saver',
		name: 'markdownSaver',
		icon: 'file:markdownSaver.svg',
		group: ['output'],
		version: 1,
		subtitle: '={{$parameter["operation"]}}',
		description: 'Save JSON data to Markdown file with character filtering',
		defaults: {
			name: 'Markdown Saver',
		},
		inputs: ['main'],
		outputs: ['main'],
		usableAsTool: true,
		properties: [
			{
				displayName: 'Operation',
				name: 'operation',
				type: 'options',
				noDataExpression: true,
				options: [
					{
						name: 'Convert to Markdown',
						value: 'convert',
						action: 'Convert JSON to markdown',
					},
				],
				default: 'convert',
			},
			{
				displayName: 'Input Data',
				name: 'inputData',
				type: 'json',
				default: '={{$json}}',
				description: 'The JSON data to convert to Markdown',
				required: true,
			},
			{
				displayName: 'Markdown Template',
				name: 'markdownTemplate',
				type: 'string',
				typeOptions: {
					rows: 5,
				},
				default: '',
				description: 'Custom template for markdown. Use {{ $JSON.key }} syntax. Leave empty for automatic Markdown conversion',
				placeholder: '# {{ $json.title }}\n\n{{ $json.content }}',
			},
			{
				displayName: 'Conversion Options',
				name: 'conversionOptions',
				type: 'collection',
				default: {},
				options: [
					{
						displayName: 'Format',
						name: 'format',
						type: 'options',
						options: [
							{
								name: 'Auto (Table/List)',
								value: 'auto',
							},
							{
								name: 'Table',
								value: 'table',
							},
							{
								name: 'List',
								value: 'list',
							},
							{
								name: 'JSON Code Block',
								value: 'codeblock',
							},
						],
						default: 'auto',
						description: 'How to format the markdown output',
					},
					{
						displayName: 'Include Headers',
						name: 'includeHeaders',
						type: 'boolean',
						default: true,
						description: 'Whether to include headers in table format',
					},
				],
			},
			{
				displayName: 'Character Filtering',
				name: 'characterFiltering',
				type: 'collection',
				default: {},
				options: [
					{
						displayName: 'Custom Find and Replace',
						name: 'customReplacements',
						type: 'fixedCollection',
						typeOptions: {
							multipleValues: true,
						},
						default: [],
						options: [
							{
								name: 'replacements',
								displayName: 'Replacement',
								values: [
									{
										displayName: 'Find',
										name: 'find',
										type: 'string',
										default: '',
									},
									{
										displayName: 'Replace With',
										name: 'replace',
										type: 'string',
										default: '',
									},
								],
							},
						],
					},
					{
						displayName: 'Escape Markdown Special Characters',
						name: 'escapeMarkdown',
						type: 'boolean',
						default: false,
						description: 'Whether to escape markdown characters like #, *, _, etc',
					},
					{
						displayName: 'Remove Carriage Returns',
						name: 'removeCarriageReturns',
						type: 'boolean',
						default: false,
						description: 'Whether to replace escaped carriage returns with empty string',
					},
					{
						displayName: 'Remove Newlines',
						name: 'removeNewlines',
						type: 'boolean',
						default: false,
						description: 'Whether to replace escaped newlines with a space',
					},
					{
						displayName: 'Unescape Quotes',
						name: 'unescapeQuotes',
						type: 'boolean',
						default: false,
						description: 'Whether to replace escaped double quotes',
					},
					{
						displayName: 'Unescape Single Quotes',
						name: 'unescapeSingleQuotes',
						type: 'boolean',
						default: false,
						description: 'Whether to replace escaped single quotes',
					},
				],
			},
			{
				displayName: 'Output Options',
				name: 'outputOptions',
				type: 'collection',
				default: {},
				options: [
					{
						displayName: 'Output Mode',
						name: 'outputMode',
						type: 'options',
						options: [
							{
								name: 'JSON Property',
								value: 'json',
								description: 'Add markdown as a property in the JSON output',
							},
							{
								name: 'Binary File',
								value: 'binary',
								description: 'Create a binary file object for n8n file nodes',
							},
						],
						default: 'json',
						description: 'How to output the markdown content',
					},
					{
						displayName: 'Property Name',
						name: 'propertyName',
						type: 'string',
						default: 'markdown',
						displayOptions: {
							show: {
								outputMode: ['json'],
							},
						},
						description: 'Name of the property to store the markdown content',
					},
					{
						displayName: 'File Name',
						name: 'fileName',
						type: 'string',
						default: 'output.md',
						displayOptions: {
							show: {
								outputMode: ['binary'],
							},
						},
						description: 'Name of the markdown file',
					},
				],
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
			const operation = this.getNodeParameter('operation', itemIndex) as string;

			if (operation === 'convert') {
				// Get input data
				const inputData = this.getNodeParameter('inputData', itemIndex) as string | object;
				const markdownTemplate = this.getNodeParameter('markdownTemplate', itemIndex) as string;
				const conversionOptions = this.getNodeParameter('conversionOptions', itemIndex) as {
					format?: string;
					includeHeaders?: boolean;
				};
				const characterFiltering = this.getNodeParameter('characterFiltering', itemIndex) as {
					removeNewlines?: boolean;
					removeCarriageReturns?: boolean;
					unescapeQuotes?: boolean;
					unescapeSingleQuotes?: boolean;
					escapeMarkdown?: boolean;
					customReplacements?: {
						replacements?: Array<{ find: string; replace: string }>;
					};
				};
				const outputOptions = this.getNodeParameter('outputOptions', itemIndex) as {
					outputMode: 'json' | 'binary';
					propertyName?: string;
					fileName?: string;
				};

				// Parse input data
				let jsonData: unknown;
				if (typeof inputData === 'string') {
					try {
						jsonData = JSON.parse(inputData);
					} catch {
						jsonData = inputData;
					}
				} else {
					jsonData = inputData;
				}

				// Convert to markdown
				let markdownContent: string;
				if (markdownTemplate && markdownTemplate.trim()) {
					// Use custom template
					markdownContent = applyTemplate(markdownTemplate, jsonData);
				} else {
					// Auto-convert based on format
					const format = conversionOptions.format || 'auto';
					markdownContent = autoConvertToMarkdown(jsonData, format, conversionOptions.includeHeaders !== false);
				}

				// Apply character filtering
				markdownContent = applyCharacterFiltering(markdownContent, characterFiltering);

				// Prepare output
				let newItem: INodeExecutionData;

				if (outputOptions.outputMode === 'binary') {
					// Create binary data
					const fileName = outputOptions.fileName || 'output.md';
					const binaryData = Buffer.from(markdownContent, 'utf8');
					
					// Use n8n's prepareBinaryData helper
					const preparedBinaryData = await this.helpers.prepareBinaryData(
						binaryData,
						fileName,
						'text/markdown'
					);
					
					newItem = {
						json: items[itemIndex].json,
						binary: { data: preparedBinaryData },
						pairedItem: { item: itemIndex },
					};
				} else {
					// Add as JSON property
					const propertyName = outputOptions.propertyName || 'markdown';
					newItem = {
						json: {
							...items[itemIndex].json,
							[propertyName]: markdownContent,
						},
						pairedItem: { item: itemIndex },
					};
				}

				returnData.push(newItem);
			}
		}

		return [returnData];
	}
}