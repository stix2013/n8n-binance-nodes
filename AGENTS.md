# Agent Development Guidelines

Essential guidelines for agentic coding agents in the `n8n-binance-nodes` repository.

## Environment
- **API (Python)**: >=3.14, FastAPI, Pydantic v2, `uv` or `pip` in `.venv`
- **Nodes (TS)**: n8n 2.8.3, BunJS 1.3.6
- **Docker**: n8n, PostgreSQL 16, API
- **AI Models**: 
  - Local: Ollama (`glm-4`, `phi-4`)
  - Cloud: Google Gemini (`gemini-2.0-flash`)

## Project Structure
- `/api/src/`: FastAPI implementation
- `/api/tests/`: Pytest suite
- `/nodes/@stix/`: Custom n8n community nodes
- `/docs/workflows/`: n8n workflow JSON exports (Versioned: D=Fixed, E=Refactored, F=Multi-Agent)
- `/scripts/`: Python/TS build and environment tools
- `/dockers/`: Dockerfiles and infrastructure config

## Commands

### API (`/api/`)
```bash
source .venv/bin/activate && pip install -e .[dev]
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
ruff check . && ruff format .           # Lint & format
python -m pytest --cov=src --cov-report=term-missing  # Test + coverage
```

### Nodes (`/nodes/@stix/n8n-nodes-binance-kline/`)
```bash
bun install && bun run build && bun run lint
```

### Docker & Environment
```bash
bun start                       # Start all services + Zrok tunnel
bun stop                        # Stop all services
bun run build:images            # Build all Docker images
docker compose restart n8n      # Pick up node changes
docker compose logs -f api      # View API logs
```

### Workflow Generation
```bash
python scripts/build_analyse_f.py  # Generate multi-agent version F
```

## Code Style & Standards

### Python
- **Naming**: `snake_case` (files/funcs/vars), `PascalCase` (classes), `UPPER_CASE` (constants)
- **Imports**: stdlib → third-party → local
- **Types**: Python 3.10+ hints (`list[str]`, `str | None`)
- **Pydantic**: Use `BaseModel` with `Field` descriptions for AI clarity

### TypeScript (n8n Nodes)
- **Structure**: Use `INodeType`, separate complex operations to `/operations/`
- **Credentials**: `ICredentialType`, ensure `password: true` for secrets
- **Validation**: Use `NodeOperationError` or `NodeApiError` for helpful n8n feedback

### AI Workflows (n8n)
- **Architecture**: Prefer Parallel Agents + Supervisor pattern for complex tasks
- **Output**: Use `outputParserStructured` (JSON) for sub-agents, Markdown for final reports
- **Credentials**: 
  - Binance: `tmVGRcPSpJIYsaeS`
  - Telegram: `O5JL1UG87JJ1GySx`
  - Ollama: `URvt83r3fqd9q5Z7`

## Workflow Policy
- **Branching**: Use `git worktree add ../worktrees/<branch>` (NEVER commit directly to main)
- **Commits**: Prefixes `feat/`, `fix/`, `docs/`, `refactor/`
- **Verification**: All changes via PR; build, lint, and tests must pass

## Security
- **Secrets**: No hardcoded keys. Use `.env` + `pydantic-settings`
- **Data**: Validate all external data using Pydantic or n8n schemas

## Troubleshooting
- [Integration Testing Architecture](docs/problems/2026-02-04-integration-testing-architecture.md)
- [n8n File Write Permissions](docs/problems/2026-02-13-n8n-file-write-permissions.md)
- [Binance URL Option Build Issue](docs/problems/2026-02-17-binance-url-option.md)
