# Agent Development Guidelines

Essential guidelines for agentic coding agents in the `n8n-binance-nodes` repository.

## Environment & Prerequisites
- **API (Python)**: >=3.13.9, FastAPI, Pydantic v2. Use `uv` or `pip` in `.venv`.
- **Nodes (TS)**: n8n 2.4.4, BunJS 1.3.6.
- **Docker**: Containerized deployment for n8n, PostgreSQL, and API.

## Build, Lint, and Test Commands

### API (from `/api/` directory)
```bash
# Setup & Run
source .venv/bin/activate && pip install -e .[dev]
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Linting & Formatting (uses Ruff)
ruff check .      # Lint
ruff format .     # Format

# Testing (pytest)
python -m pytest                                       # All tests
python -m pytest tests/test_binance_api.py             # Single file
python -m pytest tests/test_binance_api.py::test_func  # Single test
python -m pytest --cov=src --cov-report=term-missing   # Coverage
```

### n8n Nodes (from `/nodes/@stix/n8n-nodes-binance-kline/`)
```bash
bun install        # Install dependencies
bun run build      # Build TypeScript to dist/
bun run lint       # Lint code (eslint)
```

### Docker
```bash
docker compose up --build -d  # Start all services
docker compose restart n8n    # Pick up custom node changes
docker compose logs -f api    # View API logs
```

## Code Style Guidelines

### Python (FastAPI + Pydantic v2)
- **Naming**: `snake_case` for files/functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- **Imports**: Group standard library, third-party (FastAPI, Pydantic), and local modules.
- **Types**: Use Python 3.10+ type hints (`list[str]`, `str | None`).
- **Pydantic**: Use `BaseModel` and `Field`. Use `@field_validator` for custom logic.
- **FastAPI**: Use `APIRouter`, define `response_model`, and handle errors via `HTTPException`.
- **Async**: Prefer `httpx.AsyncClient` for external calls. Use `async with` context managers.

```python
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from fastapi import HTTPException

class PriceRequest(BaseModel):
    symbol: str = Field(..., pattern=r"^[A-Z0-9]+$")
    
    @field_validator('symbol')
    @classmethod
    def to_upper(cls, v: str) -> str:
        return v.upper()
```

### TypeScript (n8n Nodes)
- **Naming**: `camelCase` for variables/functions, `PascalCase` for classes.
- **Formatting**: (Prettier) `useTabs: true`, `tabWidth: 2`, `singleQuote: true`, `semi: true`, `printWidth: 100`.
- **Node Structure**: Implement `INodeType`. Separate operations into `/operations/` if complex.
- **Credentials**: Implement `ICredentialType`, use `password: true` for secrets.

## Error Handling & Logging
- **API**: Use structured JSON logging. Catch specific exceptions (e.g., `httpx.HTTPStatusError`) and map to `HTTPException`.
- **Nodes**: Use `NodeOperationError` or `NodeApiError` for user-facing errors.
- **Logging**: Level configurable via `API_LOG_LEVEL`. Avoid logging PII or secrets.

## Project Structure
- `/api/src/`: FastAPI implementation (routes, models, utils).
- `/api/tests/`: Pytest suite.
- `/nodes/@stix/`: Custom n8n node packages.
- `/dockers/`: Dockerfiles and task runner configurations.
- `.env`: Global configuration (ports, versions, keys).

## Development Workflow
- **Branching Strategy**: Always create a new branch for any new features or bug fixes. NEVER commit directly to the `main` branch.
- **Branch Naming**: Use descriptive prefixes:
  - `feat/` for new features
  - `fix/` for bug fixes
  - `docs/` for documentation changes
  - `refactor/` for code refactoring
- **Pull Requests**: All changes must be submitted via Pull Request. Ensure the build passes and the code follows the project's style guidelines before merging.

## Security & Best Practices
- **Secrets**: Never hardcode keys. Use `.env` and `pydantic-settings`.
- **Dotfiles**: Agents are allowed to read `.env` at the root for dev/test credentials.
- **I/O**: Use async/await for all network/file operations in API.
- **Validation**: Validate all external data (Binance API responses, user input) via Pydantic or n8n schemas.
