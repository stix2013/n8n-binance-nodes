# Agent Development Guidelines

Essential guidelines for agentic coding agents in the `n8n-binance-nodes` repository.

## Environment
- **API (Python)**: >=3.12, FastAPI, Pydantic v2, Celery, `uv` or `pip` in `.venv`
- **Nodes (TS)**: n8n 2.9.2, BunJS 1.3.6
- **Docker**: n8n, PostgreSQL 16, Redis 7, API
- **AI Models**: 
  - Local: Ollama (`glm-4`, `phi-4`)
  - Cloud: Google Gemini (`gemini-2.0-flash`)

## Project Structure
- `/api/src/`: FastAPI implementation
- `/api/src/tasks/`: (Deprecated - tasks now handled via `celery_client` to `crypto-analysis` worker)
- `/api/src/services/celery_client.py`: Celery client for task dispatching
- `/api/src/routes/tasks.py`: API endpoints for triggering background tasks
- `/api/tests/`: Pytest suite
- `/nodes/@stix/`: Custom n8n community nodes
- `/docs/workflows/`: n8n workflow JSON exports (Versioned: D=Fixed, E=Refactored, F=Multi-Agent)
- `/scripts/`: Python/TS build and environment tools
- `/dockers/`: Dockerfiles and infrastructure config

## Architecture: Celery & crypto-analysis
This project acts as a **Celery Client**, while the `crypto-analysis` project acts as the **Celery Worker**.
- **Broker**: Redis (`redis://redis:6379/0`)
- **Task Dispatch**: FastAPI sends tasks via `celery_client.send_task(task_name, ...)`
- **Task Names**: Must match those defined in `crypto-analysis` (e.g., `train_model`, `fetch_market_data`)
- **Integration**: The `api` service often mounts `crypto-analysis` as a volume or expects it to be in `PYTHONPATH` for certain operations.

## Commands

### API (`/api/`)
```bash
source .venv/bin/activate && pip install -e .[dev]
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
# Note: Celery worker is typically run from the crypto-analysis project
ruff check . && ruff format .           # Lint & format
python -m pytest --cov=src --cov-report=term-missing  # Test + coverage
```

### Celery Task Control (via curl)
```bash
# Trigger model training
curl -X POST http://localhost:8000/api/tasks/train-model -H "Content-Type: application/json" -d '{"symbol": "ETHUSDT", "interval": "15m", "bars": 5000}'

# Check task status
curl http://localhost:8000/api/tasks/{task_id}

# Trigger market data fetch
curl -X POST http://localhost:8000/api/tasks/fetch-market-data -H "Content-Type: application/json" -d '{"symbol": "BTCUSDT", "interval": "1h", "bars": 1000}'
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

## Development Workflow

### Task Management
1. **Plan First**: Write detailed plan to `tasks/todo.md` with checkable items before starting
2. **Verify Plan**: Check in with user before starting implementation on non-trivial tasks
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after any corrections

### Workflow Orchestration
- **Worktree First**: ALWAYS create a git worktree before bug fixes or new features (never commit directly to main)
- **Naming**: Use `fix/<issue>` or `feat/<feature>` branch names
- **Plan Mode**: Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- **Subagent Strategy**: Use subagents for research, exploration, and parallel analysis
- **Self-Improvement**: After ANY correction from user, update `tasks/lessons.md` with the pattern
- **Verification**: Never mark complete without proving it works (run tests, check logs)
- **Elegance**: For non-trivial changes, pause and ask "is there a more elegant way?"
- **Bug Fixing**: Create worktree first, then fix - go fix failing tests without being told how

### Branching & Commits
- **Commits**: Prefixes `feat/`, `fix/`, `docs/`, `refactor/`
- **Verification**: All changes via PR; build, lint, and tests must pass

## Security
- **Secrets**: No hardcoded keys. Use `.env` + `pydantic-settings`
- **Data**: Validate all external data using Pydantic or n8n schemas

## Troubleshooting
- [Integration Testing Architecture](docs/problems/2026-02-04-integration-testing-architecture.md)
- [n8n File Write Permissions](docs/problems/2026-02-13-n8n-file-write-permissions.md)
- [Binance URL Option Build Issue](docs/problems/2026-02-17-binance-url-option.md)
- [n8n Behind Zrok Reverse Proxy](docs/problems/2026-02-27-n8n-zrok-proxy.md)

## Lessons Learned

### External Task Runners Configuration
- **Simplified Architecture**: Use external runners without queue mode (no n8n-worker/redis)
- **Runners Mode**: Use `N8N_RUNNERS_MODE=external` for separate task-runners container
- **Broker Bind Address**: Must bind to `0.0.0.0` (not `127.0.0.1`) for external runners to connect - use `N8N_RUNNERS_BROKER_LISTEN_ADDRESS=0.0.0.0`
- **Dockerfile Naming**: Use `Dockerfile.runners` in `/dockers/` for clarity
- **Build Context**: Task-runners build context must be `.` (project root), not `./dockers`
- **Healthcheck Port**: Task-runners healthcheck uses port 5680 (not 5679)

### Model Training & Celery
- **CPU-only PyTorch**: Use `--index-url https://download.pytorch.org/whl/cpu` for much smaller Docker images (~500MB vs 3GB+).
- **PYTHONPATH**: Celery requires the source directory (e.g., `/app`) to be in `PYTHONPATH` to resolve task modules like `src.tasks.training`.
- **Torch Pickling**: `torch.device` objects are not picklable. Use custom `__getstate__` and `__setstate__` to exclude them during serialization and restore them after.
- **Port Isolation**: When running multiple stacks (e.g., in a worktree), use isolated host ports for Redis (6380) and Postgres (5433) to avoid conflicts.

### Deprecation Warnings Fix
- Add `N8N_MIGRATE_FS_STORAGE_PATH=true` for binaryData → storage migration
- **Do NOT add**: `OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS=true` - only needed for queue mode
