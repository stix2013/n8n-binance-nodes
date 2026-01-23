# Research Report: Creating Custom n8n Nodes

## Executive Summary

Creating custom n8n nodes allows developers to extend the platform's capabilities beyond its 400+ built-in integrations. This comprehensive guide covers the complete development lifecycle tailored for modern development stacks, including BunJS, Docker-based workflows, and AI-assisted development tools. The process involves setting up a proper TypeScript/JavaScript development environment using BunJS 1.3.6, implementing node base files with resource and operation definitions, creating credential types for authentication, and thorough testing with n8n 2.5.0. The investment typically ranges from a few hours for simple API integrations to several days for complex nodes with multiple authentication methods and operations.

## Technical Overview

### Core Concepts and Architecture

n8n nodes are modular components that perform specific operations within workflow automation pipelines. Each node operates as an Extract, Transform, Load (ETL) unit, receiving data from previous nodes, processing it according to configured parameters, and passing results to subsequent nodes. The fundamental data structure in n8n is an array of objects, where each object represents an item flowing through the workflow. Nodes communicate through this standardized data format, enabling seamless chaining of operations across different services and APIs.

The n8n architecture distinguishes between several node types: trigger nodes that initiate workflows based on events or schedules, regular nodes that process data and make API calls, and logic nodes that control workflow branching and iteration. Custom nodes typically fall into the regular node category, connecting to external APIs or performing custom data transformations. The platform handles authentication, credential management, and HTTP request execution through built-in helpers, allowing node developers to focus on business logic.

Node functionality is defined through a description object that specifies display properties, parameters, authentication requirements, and operational capabilities. The description uses TypeScript interfaces from the `n8n-workflow` package to ensure type safety and provide IDE autocomplete support. Operations are organized by resources, allowing a single node to handle multiple endpoint categories (e.g., a GitHub node managing repos, issues, and users as separate resources with distinct operations).

### Key Features and Capabilities

Custom n8n nodes support sophisticated functionality including multiple authentication mechanisms (API keys, OAuth2, basic auth, header auth), dynamic parameter rendering based on other field selections, batch processing of multiple input items, and error handling with custom error messages. The platform provides built-in helpers for HTTP requests that automatically handle authentication credentials, follow redirects, and manage request timeouts. Nodes can define multiple output channels for different operation results, enabling complex branching logic within a single node.

The n8n-node CLI tool generates scaffolded projects with proper file structure, TypeScript configuration, linting rules, and testing setup. This tooling ensures consistency with n8n's internal standards and simplifies the submission process for verified community node status. The generated structure includes separate files for node logic, credentials, and translation resources, following a modular design that facilitates maintenance and testing.

## Detailed Analysis

### Development Environment Setup

The prerequisite environment for n8n node development requires **BunJS 1.3.6** or higher (as a faster alternative to Node.js), Docker 29.1.5 for containerization, and git for version control. Our specific stack uses:

- **BunJS 1.3.6**: For package management and script execution (significantly faster than npm)
- **Docker 29.1.5**: For running n8n 2.5.0 locally and N8N Runners 2.5.0 for execution scaling
- **n8n 2.5.0**: The target platform version for node development
- **Python 3.19.3**: Available in Docker for Code node scripting when needed
- **OpenCode 1.1.31 with MCP n8n-mcp**: For AI-assisted node development with direct n8n integration

The recommended approach for creating new nodes uses the `@n8n/create-node` initializer with BunJS:

```bash
bun create @n8n/node@latest
```

This command prompts for the node name, display name, and scope (personal namespace or organization), then generates a complete project with package.json, TypeScript configuration, and scaffolded node files. The generated project includes scripts for building, linting, and testing the node. For local development, the `bun run start` command compiles TypeScript and reloads the node, allowing rapid iteration.

For developers preferring a more integrated development experience, **OpenCode 1.1.31 with MCP n8n-mcp** provides direct integration with your n8n instance, enabling:

- Real-time node template generation
- Credential testing from the IDE
- Workflow simulation without leaving the editor
- Automated documentation generation based on node descriptions

### n8n 2.5.0 Docker Configuration

For our specific stack using Docker 29.1.5, create a dedicated development setup:

```yaml
# docker-compose.yml for n8n 2.5.0 development
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:2.5.0
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=dev
      - N8N_BASIC_AUTH_PASSWORD=dev
      - N8N_COMMUNITY_PACKAGES_ENABLED=true
      - N8N_CUSTOM_EXTENSIONS=/home/node/.n8n/custom/
      - N8N_ENCRYPTION_KEY=develop_encryption_key
    volumes:
      - n8n_data:/home/node/.n8n
      - ./custom-nodes:/home/node/.n8n/custom
    restart: unless-stopped

  n8n-runner:
    image: docker.n8n.io/n8nio/n8n:2.5.0
    command: n8n worker
    environment:
      - N8N_ENCRYPTION_KEY=develop_encryption_key
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
    volumes:
      - ./custom-nodes:/home/node/.n8n/custom
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  n8n_data:
```

Mount your custom nodes directory to `~/.n8n/custom` for live testing. During development, monitor logs with:

```bash
docker-compose logs -f n8n
```

### Node File Structure

The official file structure for n8n community nodes follows specific conventions that enable proper discovery, installation, and execution. At the root level, the `package.json` must include the `n8n-nodes-` prefix in the package name (or `@scope/n8n-nodes-` for scoped packages), specify the n8n version compatibility, and declare the node entry point. The main entry point exports both the node class and any credential types defined in the package.

The `nodes` directory contains the primary node implementation files. Each node gets its own subdirectory with a base file named `<node-name>.node.ts` containing the node class definition. This file implements the `INodeType` interface and defines the description object containing display name, version, properties, and operations. For complex nodes supporting multiple resources, the base file imports operation-specific logic from separate files in an `operations` subdirectory.

The `credentials` directory stores credential type definitions for API authentication. Each credential type gets its own file implementing the `ICredentialType` interface, defining required fields (API keys, client secrets, tokens) and authentication property mapping. The credential type name must match references in the node's description object for proper binding during workflow execution.

Optional directories include `methods` for helper functions used across operations, `transport` for HTTP client configuration, and language-specific translation files for internationalization. The project structure accommodates single-node packages (most common) and multi-node packages for related functionality, with the same conventions applying to each contained node.

### Node Base File Implementation

The node base file serves as the core of any n8n custom node, implementing the `INodeType` interface and defining all aspects of node behavior. The implementation uses TypeScript classes with a `description` property of type `INodeTypeDescription` containing configuration for display, parameters, and operations. The basic structure follows this pattern:

```typescript
import { INodeType, INodeTypeDescription } from "n8n-workflow";

export class ExampleNode implements INodeType {
  description: INodeTypeDescription = {
    displayName: "Example Node",
    name: "example",
    group: ["transform"],
    version: 1,
    description: "Perform example operations on data",
    defaults: {
      name: "Example Node",
    },
    inputs: ["main"],
    outputs: ["main"],
    credentials: [],
    properties: [],
  };
}
```

The `displayName` appears in the n8n editor nodes panel, while `name` serves as the programmatic identifier used in workflow JSON. The `group` array categorizes the node for filtering in the editor. For nodes requiring authentication, the `credentials` array references credential type files by name, with optional `displayOptions` for showing different credential types based on authentication method selection.

### Resources and Operations Organization

Organizing node functionality by resources and operations creates a logical structure that mirrors REST API design and improves user experience. Resources represent major entity types (users, orders, files) while operations represent actions on those resources (create, get, list, delete). This organization uses nested options in the properties array:

```typescript
properties: [
  {
    displayName: "Resource",
    name: "resource",
    type: "options",
    options: [
      { name: "User", value: "user" },
      { name: "Order", value: "order" },
    ],
    default: "user",
  },
  {
    displayName: "Operation",
    name: "operation",
    type: "options",
    displayOptions: {
      show: {
        resource: ["user"],
      },
    },
    options: [
      { name: "Create", value: "create" },
      { name: "Get", value: "get" },
    ],
    default: "create",
  },
];
```

This pattern enables n8n's dynamic parameter rendering—selecting "User" as the resource automatically shows only user-related operations while hiding order operations. Each operation property uses `displayOptions` with the `show` key to specify which resource values trigger its visibility. The `default` property sets initial values for auto-completed workflows.

### Authentication and Credentials

n8n provides a robust credential management system that securely stores and injects authentication details during node execution. Custom nodes define credential types that specify required fields and how those credentials map to HTTP request properties (headers, query parameters, body fields, or auth headers). The credential system supports multiple authentication methods for the same node, allowing users to choose between API keys, OAuth2, or basic auth based on the target service's capabilities.

The credential type file implements `ICredentialType` with a name property matching references in the node description, display name for the credentials panel, and a properties array defining required fields:

```typescript
import { ICredentialType, INodeProperties } from "n8n-workflow";

export class ExampleNodeApi implements ICredentialType {
  name = "exampleNodeApi";
  displayName = "Example Node API";
  properties: INodeProperties[] = [
    {
      displayName: "API Key",
      name: "apiKey",
      type: "string",
      typeOptions: {
        password: true,
      },
      default: "",
    },
  ];
}
```

The `authenticate` property defines how credentials transform into HTTP request modifications. For query parameter authentication:

```typescript
authenticate: {
	type: 'generic',
	properties: {
		qs: {
			'api_key': '={{$credentials.apiKey}}'
		}
	}
}
```

For header-based authentication using Bearer tokens:

```typescript
authenticate: {
	type: 'generic',
	properties: {
		headers: {
			'Authorization': 'Bearer {{$credentials.accessToken}}'
		}
	}
}
```

The `test` property enables n8n to verify credential validity during setup by making a test request to the API:

```typescript
test: {
	request: {
		baseURL: '={{$credentials.domain}}',
		url: '/verify'
	}
}
```

### Execute Method Implementation

Programmatic-style nodes implement an `execute` method that processes input data and generates output. The method receives execution context through the `this` parameter and returns a promise resolving to processed output data. The basic pattern iterates over input items, applies node parameters, and returns modified data:

```typescript
async execute(this: IExecuteFunctions): Promise<INodeExecutionData[]> {
	const items = this.getInputData();
	const returnData: INodeExecutionData[] = [];

	for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
		const resource = this.getNodeParameter('resource', itemIndex);
		const operation = this.getNodeParameter('operation', itemIndex);

		if (resource === 'user' && operation === 'create') {
			const name = this.getNodeParameter('name', itemIndex);
			const email = this.getNodeParameter('email', itemIndex);

			const response = await this.helpers.httpRequest({
				method: 'POST',
				url: `https://api.example.com/users`,
				body: { name, email }
			});

			returnData.push({ json: response });
		}
	}

	return this.prepareOutputData(returnData);
}
```

The `getInputData` method retrieves the array of items from the previous node. The `getNodeParameter` method retrieves user-configured values, supporting expressions that reference other fields or previous node data. The `httpRequest` helper makes authenticated HTTP calls, automatically using credentials attached to the node. The `prepareOutputData` method transforms the return array into n8n's standardized output format.

For operations requiring authentication mapping through the credential system, use `httpRequestWithAuthentication`:

```typescript
const response = await this.helpers.httpRequestWithAuthentication.call(
  this,
  "exampleNodeApi",
  {
    method: "GET",
    url: "https://api.example.com/resource",
  },
);
```

### Error Handling and Validation

Robust error handling improves the user experience by providing meaningful feedback when operations fail. The execute method should catch specific error types and throw `NodeOperationError` or `NodeApiError` instances with descriptive messages:

```typescript
try {
  const response = await this.helpers.httpRequest(options);
} catch (error) {
  if (error.statusCode === 404) {
    throw new NodeOperationError(this.getNode(), "Resource not found", {
      itemIndex,
    });
  }
  throw new NodeApiError(this.getNode(), error, { itemIndex });
}
```

Input validation uses the property definition's built-in constraints (required fields, type validation) and custom validation through the `validateInput` method. For complex validation logic, implement additional checks before making API calls and throw descriptive errors when validation fails.

## Practical Considerations

### Implementation Effort Estimates

Simple API integration nodes with basic CRUD operations typically require **4-8 hours** of development effort for experienced TypeScript developers using BunJS. This includes project setup, implementing 2-3 operations across 1-2 resources, basic authentication, and local testing with n8n 2.5.0. The scaffolding generated by the n8n-node tool significantly reduces boilerplate code, allowing focus on API-specific logic.

Complex nodes with multiple authentication methods, extensive operation sets, and dynamic resource loading require **2-5 days** of development. These nodes benefit from the programmatic-style approach, separating operation logic into dedicated files for maintainability. Authentication complexity increases development time, particularly for OAuth2 flows requiring token refresh handling and multiple credential type definitions.

Testing with **N8N Runners 2.5.0** adds scalability validation, ensuring nodes perform correctly in distributed execution environments. Testing and documentation typically add 50-100% additional time to the core implementation.

### AI-Assisted Development with OpenCode MCP

Using **OpenCode 1.1.31 with MCP n8n-mcp** integration can reduce development time by 30-40% through:

- **Auto-generation of node scaffolding**: Based on API specifications
- **Real-time credential testing**: Without leaving the IDE
- **Automated parameter validation**: AI-suggested property definitions
- **Documentation generation**: From code comments and API docs
- **Workflow simulation**: Test nodes in context before deployment

Example MCP workflow:

1. Provide OpenCode with your API's OpenAPI spec
2. MCP n8n-mcp generates initial node structure
3. Iterate on operations with AI-assisted completion
4. Test credentials and operations directly from IDE
5. Deploy to local n8n 2.5.0 instance with one command

### Learning Curve Assessment

Developers familiar with TypeScript and REST APIs can become productive with n8n node development within a few hours. The official documentation provides comprehensive guidance, and the n8n-node CLI generates standards-compliant code that reduces learning curve friction. Understanding the data flow between nodes and the description object structure are the primary concepts to master.

The declarative-style node approach (using routing in properties) requires less code but can become complex for nodes with many operations. The programmatic-style approach offers more flexibility but requires implementing the execute method with explicit iteration and parameter handling. Most developers find the programmatic style more intuitive once they understand the basic pattern.

### Operational Requirements

Self-hosted n8n 2.5.0 instances require enabling community nodes in the Docker configuration:

```yaml
environment:
  - N8N_COMMUNITY_PACKAGES_ENABLED=true
  - N8N_CUSTOM_EXTENSIONS=/home/node/.n8n/custom/
```

Custom nodes must be installed in the `~/.n8n/custom` directory (or the directory specified by `N8N_CUSTOM_EXTENSIONS`). The node package must be built (TypeScript compiled to JavaScript) before installation. During development, use BunJS watch mode for rapid iteration:

```bash
bun run build --watch
```

Production deployment with **N8N Runners 2.5.0** requires the node package to be published to npm (for community distribution) or installed locally from a private registry. Verified community nodes appear in n8n's built-in node panel for users who have enabled community node discovery, simplifying installation for end users.

## Comparative Analysis

### Declarative vs. Programmatic Style

The declarative approach uses the `routing` property in parameter definitions to map operations to execute methods or URLs. This style reduces boilerplate for simple integrations but requires understanding the routing configuration structure. It's best suited for nodes making simple HTTP requests with minimal transformation logic.

The programmatic approach implements an explicit `execute` method with full control over data processing, HTTP requests, and error handling. This style supports complex logic including conditional API calls, data aggregation from multiple sources, and custom transformation pipelines. Most production nodes use this approach for its flexibility and maintainability.

### Custom Nodes vs. Code Node

The n8n Code node allows JavaScript or Python execution within workflows without creating a separate package. For simple transformations or one-off API calls, the Code node may be more appropriate than building a full custom node. However, Code node scripts aren't reusable across workflows and don't benefit from the n8n editor's parameter UI generation.

Custom nodes are justified when the functionality will be used across multiple workflows, requires a user-friendly configuration interface, or should be shared with the n8n community. The initial investment in creating a proper node package pays dividends through reusability, easier configuration, and distribution capabilities.

### BunJS vs. Node.js for Node Development

**BunJS 1.3.6** offers significant advantages for n8n node development:

- **5x faster package installation** compared to npm
- **Built-in TypeScript compilation** without separate tsc
- **Native watch mode** for development
- **Smaller Docker images** when building custom n8n images

Compatibility note: n8n itself still runs on Node.js within its Docker container, but using BunJS for development tooling and building node packages is fully compatible.

## Recommendations

### Getting Started Approach

For first-time node developers using our specific stack:

1. **Environment Setup**:

   ```bash
   # Install BunJS 1.3.6
   curl -fsSL https://bun.sh/install | bash

   # Clone starter repository
   git clone https://github.com/n8n-io/n8n-nodes-starter.git
   cd n8n-nodes-starter

   # Install dependencies with Bun
   bun install
   ```

2. **Configure OpenCode 1.1.31**:
   - Install MCP n8n-mcp extension
   - Connect to local n8n 2.5.0 instance
   - Configure autocomplete for n8n-workflow package

3. **Docker Development**:

   ```bash
   # Start n8n 2.5.0 with custom nodes mounting
   docker-compose up -d

   # Watch for changes and rebuild
   bun run build --watch
   ```

4. **Build a simple node** (like a weather service or currency converter) as a first project to learn the patterns before tackling complex integrations.

### Best Practices Summary

- **Use BunJS 1.3.6** for all development tasks (install, build, test)
- **Structure node code** by separating operations into dedicated files for maintainability
- **Test with N8N Runners 2.5.0** to ensure scalability
- **Implement comprehensive error handling** with descriptive error messages
- **Leverage OpenCode MCP** for AI-assisted development
- **Document all operations** and parameters with clear descriptions
- **Follow community node standards** from the start if verification is a goal
- **Pin n8n dependency** to `~2.5.0` in package.json for version compatibility

### Risk Mitigation

**Version compatibility**: n8n 2.5.0 uses Node.js 20 internally. Custom nodes built with BunJS 1.3.6 are compatible, but test thoroughly. Pin dependencies in package.json:

```json
{
  "n8n": {
    "n8nNodesApiVersion": 1,
    "credentials": [...],
    "nodes": [...]
  },
  "peerDependencies": {
    "n8n-workflow": "~2.5.0"
  }
}
```

**Security considerations**:

- Never log credential values
- Use n8n's credential system rather than hardcoding API keys
- Validate all input parameters before making API calls
- Ensure credentials aren't exposed in error messages or logs
- Use Python 3.19.3 sandboxes for Code node execution when needed

**MCP integration risks**: When using OpenCode MCP n8n-mcp, ensure your n8n instance is on a private network or properly authenticated to prevent unauthorized access.

## References

- n8n Documentation - Creating Nodes: https://docs.n8n.io/integrations/creating-nodes/overview/
- n8n Tutorial - Build a Programmatic-Style Node: https://docs.n8n.io/integrations/creating-nodes/build/programmatic-style-node
- Building Community Nodes Documentation: https://docs.n8n.io/integrations/community-nodes/build-community-nodes/
- Node Base File Structure Reference: https://docs.n8n.io/integrations/creating-nodes/build/reference/node-base-files/structure
- Credentials Files Reference: https://docs.n8n.io/integrations/creating-nodes/build/reference/credentials-files.md
- Code Standards and Best Practices: https://docs.n8n.io/integrations/creating-nodes/build/reference/code-standards
- Verification Guidelines: https://docs.n8n.io/integrations/creating-nodes/build/reference/verification-guidelines/
- BunJS Documentation: https://bun.sh/docs
- n8n Docker Setup: https://docs.n8n.io/hosting/installation/docker/
- OpenCode MCP n8n-mcp: https://github.com/opencode-co/n8n-mcp
