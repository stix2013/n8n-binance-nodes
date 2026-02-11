# Markdown Saver Node

## Overview
A new n8n custom node that converts JSON data to Markdown format with character filtering capabilities.

## Location
- **Worktree**: `/home/stevan/projects/AI/n8n-binance-nodes-markdown`
- **Branch**: `feat/markdown-saver-node`
- **Package**: `@stix/n8n-nodes-markdown-saver`

## Features

### JSON to Markdown Conversion
- **Automatic conversion**: Detects data structure and converts to appropriate Markdown format
  - Arrays → Tables or Lists
  - Objects → Key-value sections
  - Primitives → Plain text
- **Template support**: Use custom templates with `{{ $json.key }}` syntax
- **Multiple formats**: Auto, Table, List, or JSON Code Block

### Character Filtering
The node includes comprehensive character filtering options:
- **Remove Newlines**: Replace `\n` with a space
- **Remove Carriage Returns**: Replace `\r` with empty string
- **Unescape Quotes**: Replace `\"` with `"`
- **Unescape Single Quotes**: Replace `\'` with `'`
- **Escape Markdown Special Characters**: Escape `#`, `*`, `_`, etc.
- **Custom Find and Replace**: Define your own search/replace patterns

### Output Options
- **JSON Property**: Add markdown as a property in the output
- **Binary File**: Create a binary file object compatible with n8n file nodes

## Usage

1. **Build the node**:
   ```bash
   cd nodes/@stix/n8n-nodes-markdown-saver
   bun install
   bun run build
   ```

2. **Run with Docker**:
   ```bash
   cd /home/stevan/projects/AI/n8n-binance-nodes-markdown
   docker compose up -d
   ```

3. **Access n8n**: Open http://localhost:5678 and search for "Markdown Saver" in the nodes panel

## Configuration Example

### Simple Conversion
- Input Data: `{{ $json }}`
- Conversion Options → Format: Auto
- Character Filtering → Remove Newlines: true
- Output Options → Output Mode: JSON Property

### Custom Template
- Markdown Template: `# {{ $json.title }}\n\n{{ $json.content }}`
- Character Filtering → Unescape Quotes: true
- Output Options → Output Mode: Binary File
- File Name: `report.md`

## File Structure
```
nodes/@stix/n8n-nodes-markdown-saver/
├── nodes/
│   └── MarkdownSaver/
│       ├── MarkdownSaver.node.ts  # Main node implementation
│       └── markdownSaver.svg      # Node icon
├── package.json                    # Package configuration
├── tsconfig.json                   # TypeScript configuration
├── eslint.config.mjs              # ESLint configuration
└── dist/                          # Compiled JavaScript
```

## Technical Details

### Built With
- TypeScript 5.9.2
- n8n-workflow (peer dependency)
- @n8n/node-cli for building

### Node Properties
- **usableAsTool**: true (can be used as an AI tool)
- **Group**: output
- **Version**: 1

### Conversion Logic
The node intelligently detects the input data structure:
1. Arrays of objects with similar structure → Markdown tables
2. Arrays of mixed/primitive data → Markdown lists
3. Objects → Sectioned markdown with headers
4. Primitives → Plain text

### Character Filtering Pipeline
Filters are applied in the following order:
1. Unescape single quotes
2. Unescape double quotes
3. Remove carriage returns
4. Remove newlines
5. Escape markdown special characters
6. Apply custom replacements

## Testing

After starting the Docker containers:
1. Create a new workflow in n8n
2. Add a "Markdown Saver" node
3. Configure with sample JSON data
4. Execute and verify the markdown output

## Status
✅ Node created and built successfully
✅ ESLint validation passed
✅ Copied to worktree
✅ Docker compose updated with volume mount
⏳ Ready for testing in n8n