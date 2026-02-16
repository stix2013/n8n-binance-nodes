# Agent Development Guidelines

Essential guidelines for agentic coding agents in the `n8n-binance-nodes` repository.

## Environment
- **API (Python)**: >=3.14, FastAPI, Pydantic v2, `uv` or `pip` in `.venv`
- **Nodes (TS)**: n8n 2.6.4, BunJS 1.3.6
- **Docker**: n8n, PostgreSQL, API

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

### Docker
```bash
docker compose up --build -d    # Start all
docker compose restart n8n      # Pick up node changes
docker compose logs -f api      # View API logs
```

## Code Style

### Python: `snake_case` (files/funcs/vars), `PascalCase` (classes), `UPPER_CASE` (constants)
- Imports: stdlib → third-party → local
- Types: Python 3.10+ hints (`list[str]`, `str | None`)
- Pydantic: `BaseModel`, `Field`, `@field_validator`
- FastAPI: `APIRouter`, `response_model`, `HTTPException`
- Async: `httpx.AsyncClient` with `async with`

### TypeScript: `camelCase` (vars/funcs), `PascalCase` (classes)
- Use `INodeType`, separate complex ops to `/operations/`
- Credentials: `ICredentialType`, `password: true` for secrets

## Error Handling
- API: JSON logging, catch specific exceptions → `HTTPException`
- Nodes: `NodeOperationError` / `NodeApiError`
- Configurable log level via `API_LOG_LEVEL`, no PII/secrets

## Project Structure
`/api/src/` (FastAPI), `/api/tests/` (pytest), `/nodes/@stix/` (n8n nodes), `/dockers/` (Dockerfiles), `.env`

## Workflow
- Use `git worktree add ../worktrees/<branch>` for new branches (NEVER commit to main)
- Prefixes: `feat/`, `fix/`, `docs/`, `refactor/`
- All changes via PR (build + lint must pass)

## Security
- No hardcoded secrets → `.env` + `pydantic-settings`
- Async I/O in API, validate all external data (Pydantic/n8n schemas)

## Troubleshooting
- Integration testing: [docs/problems/2026-02-04-integration-testing-architecture.md](docs/problems/2026-02-04-integration-testing-architecture.md)
- File permissions: [docs/problems/2026-02-13-n8n-file-write-permissions.md](docs/problems/2026-02-13-n8n-file-write-permissions.md)
