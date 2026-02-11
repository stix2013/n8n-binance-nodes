"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MarkdownSaver = void 0;
function applyTemplate(template, data) {
    let result = template;
    const regex = /\{\{\s*\$json\.?(\w+|\['[^']+'\]|\["[^"]+"\])\s*\}\}/g;
    result = result.replace(regex, (match, key) => {
        const cleanKey = key.replace(/^\['|'$\]|^\["|"$\]/g, '');
        const value = getNestedValue(data, cleanKey);
        return value !== undefined ? String(value) : match;
    });
    return result;
}
function getNestedValue(obj, path) {
    const keys = path.split('.');
    let value = obj;
    for (const key of keys) {
        if (value === null || value === undefined) {
            return undefined;
        }
        if (typeof value !== 'object') {
            return undefined;
        }
        value = value[key];
    }
    return value;
}
function isTabularData(data) {
    if (data.length === 0)
        return false;
    const firstItem = data[0];
    if (typeof firstItem !== 'object' || firstItem === null)
        return false;
    const keys = Object.keys(firstItem);
    return keys.length > 0 && data.every(item => typeof item === 'object' &&
        item !== null &&
        Object.keys(item).length === keys.length);
}
function convertToTable(data, includeHeaders) {
    if (data.length === 0)
        return '';
    const keys = Object.keys(data[0]);
    let markdown = '';
    if (includeHeaders) {
        markdown += '| ' + keys.join(' | ') + ' |\n';
        markdown += '|' + keys.map(() => ' --- ').join('|') + '|\n';
    }
    for (const item of data) {
        const values = keys.map(key => {
            const value = item[key];
            if (value === null || value === undefined)
                return '';
            if (typeof value === 'object')
                return JSON.stringify(value);
            return String(value).replace(/\|/g, '\\|').replace(/\n/g, ' ');
        });
        markdown += '| ' + values.join(' | ') + ' |\n';
    }
    return markdown;
}
function convertObjectToListItem(obj) {
    const pairs = [];
    for (const [key, value] of Object.entries(obj)) {
        if (value !== null && value !== undefined) {
            if (typeof value === 'object') {
                pairs.push(`${key}: ${JSON.stringify(value)}`);
            }
            else {
                pairs.push(`${key}: ${value}`);
            }
        }
    }
    return pairs.join(', ');
}
function convertToList(data) {
    let markdown = '';
    for (const item of data) {
        if (typeof item === 'object' && item !== null) {
            markdown += '- ' + convertObjectToListItem(item) + '\n';
        }
        else {
            markdown += '- ' + String(item) + '\n';
        }
    }
    return markdown;
}
function convertObjectToMarkdown(obj) {
    let markdown = '';
    for (const [key, value] of Object.entries(obj)) {
        if (value !== null && value !== undefined) {
            markdown += `## ${key}\n\n`;
            if (typeof value === 'object') {
                if (Array.isArray(value)) {
                    markdown += convertToList(value) + '\n';
                }
                else {
                    markdown += '```json\n' + JSON.stringify(value, null, 2) + '\n```\n\n';
                }
            }
            else {
                markdown += String(value) + '\n\n';
            }
        }
    }
    return markdown;
}
function autoConvertToMarkdown(data, format, includeHeaders) {
    if (format === 'codeblock') {
        return '```json\n' + JSON.stringify(data, null, 2) + '\n```';
    }
    if (Array.isArray(data)) {
        if (data.length === 0) {
            return '*No data*';
        }
        if (format === 'table' || (format === 'auto' && isTabularData(data))) {
            return convertToTable(data, includeHeaders);
        }
        else {
            return convertToList(data);
        }
    }
    if (typeof data === 'object' && data !== null) {
        return convertObjectToMarkdown(data);
    }
    return String(data);
}
function escapeMarkdownCharacters(content) {
    return content
        .replace(/\\/g, '\\\\')
        .replace(/`/g, '\\`')
        .replace(/\*/g, '\\*')
        .replace(/_/g, '\\_')
        .replace(/\{/g, '\\{')
        .replace(/\}/g, '\\}')
        .replace(/\[/g, '\\[')
        .replace(/\]/g, '\\]')
        .replace(/\(/g, '\\(')
        .replace(/\)/g, '\\)')
        .replace(/#/g, '\\#')
        .replace(/\+/g, '\\+')
        .replace(/-/g, '\\-')
        .replace(/\./g, '\\.')
        .replace(/!/g, '\\!');
}
function applyCharacterFiltering(content, filtering) {
    var _a;
    let result = content;
    if (filtering.unescapeSingleQuotes) {
        result = result.replace(/\\'/g, "'");
    }
    if (filtering.unescapeQuotes) {
        result = result.replace(/\\"/g, '"');
    }
    if (filtering.removeCarriageReturns) {
        result = result.replace(/\\r/g, '');
    }
    if (filtering.removeNewlines) {
        result = result.replace(/\\n/g, ' ');
    }
    if (filtering.escapeMarkdown) {
        result = escapeMarkdownCharacters(result);
    }
    if ((_a = filtering.customReplacements) === null || _a === void 0 ? void 0 : _a.replacements) {
        for (const replacement of filtering.customReplacements.replacements) {
            if (replacement.find) {
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
class MarkdownSaver {
    constructor() {
        this.description = {
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
                    description: 'Custom template for markdown. Use {{ $json.key }} syntax. Leave empty for automatic Markdown conversion',
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
    }
    async execute() {
        const items = this.getInputData();
        const returnData = [];
        for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
            const operation = this.getNodeParameter('operation', itemIndex);
            if (operation === 'convert') {
                const inputData = this.getNodeParameter('inputData', itemIndex);
                const markdownTemplate = this.getNodeParameter('markdownTemplate', itemIndex);
                const conversionOptions = this.getNodeParameter('conversionOptions', itemIndex);
                const characterFiltering = this.getNodeParameter('characterFiltering', itemIndex);
                const outputOptions = this.getNodeParameter('outputOptions', itemIndex);
                let jsonData;
                if (typeof inputData === 'string') {
                    try {
                        jsonData = JSON.parse(inputData);
                    }
                    catch {
                        jsonData = inputData;
                    }
                }
                else {
                    jsonData = inputData;
                }
                let markdownContent;
                if (markdownTemplate && markdownTemplate.trim()) {
                    markdownContent = applyTemplate(markdownTemplate, jsonData);
                }
                else {
                    const format = conversionOptions.format || 'auto';
                    markdownContent = autoConvertToMarkdown(jsonData, format, conversionOptions.includeHeaders !== false);
                }
                markdownContent = applyCharacterFiltering(markdownContent, characterFiltering);
                let newItem;
                if (outputOptions.outputMode === 'binary') {
                    const fileName = outputOptions.fileName || 'output.md';
                    const binaryData = Buffer.from(markdownContent, 'utf8');
                    const preparedBinaryData = await this.helpers.prepareBinaryData(binaryData, fileName, 'text/markdown');
                    newItem = {
                        json: items[itemIndex].json,
                        binary: { data: preparedBinaryData },
                        pairedItem: { item: itemIndex },
                    };
                }
                else {
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
exports.MarkdownSaver = MarkdownSaver;
//# sourceMappingURL=MarkdownSaver.node.js.map