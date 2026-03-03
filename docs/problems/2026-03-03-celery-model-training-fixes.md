# Problem: Celery Model Training Implementation Issues

## 1. PyTorch Image Size and NVIDIA Dependencies
**Issue**: Installing the standard `torch` package resulted in a massive Docker image (~3GB) and long build times due to unnecessary CUDA/NVIDIA dependencies.
**Solution**:
- Updated `Dockerfile.python` to explicitly install the CPU-only version of PyTorch using the PyTorch index:
  ```dockerfile
  RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
  ```
- Updated `pyproject.toml` to use markers for platform-specific dependencies.
- Result: Image size reduced to ~500MB and build times significantly improved.

## 2. Celery Module Discovery (ModuleNotFoundError)
**Issue**: The Celery worker failed to start with `ModuleNotFoundError: No module named 'src'`, even though the code was present in the container.
**Solution**:
- Corrected the `PYTHONPATH` in `docker-compose.yml` to point to `/app` instead of `/app/src`.
- This ensures that `src.config.celery_app` is resolvable as a top-level package.
  ```yaml
  environment:
    - PYTHONPATH=/app:/libs/crypto-analysis/src
  ```

## 3. Binance API Connectivity (NameResolutionError)
**Issue**: Containers (API and Worker) were unable to resolve `fapi.binance.com`, leading to `ConnectError`.
**Solution**:
- Replicated the `extra_hosts` configuration from the `n8n` service to both the `api` and `celery-worker` services in `docker-compose.yml`.
- This ensures all Python services can reach the Binance API endpoints reliably.

## 4. Neural Network Input Dimension Mismatch
**Issue**: `RuntimeError: mat1 and mat2 shapes cannot be multiplied (64x71 and 50x128)`. The `OnlineNeuralNetwork` had a hardcoded `input_dim=50`, but the feature engineer produced 71 features.
**Solution**:
- Modified `crypto_analysis/online/generator.py` to use "lazy initialization" for models.
- The `input_dim` is now detected dynamically from the created features during the `fit()` call, and models are initialized with the correct dimensions.

## 5. Serialization Failures with Torch Objects (Pickle)
**Issue**: `joblib.dump` and Celery result storage failed because `torch.device` objects are not picklable. This caused the task to crash silently or return generic "exception type" errors.
**Solution**:
- Implemented `__getstate__` and `__setstate__` in `OnlineNeuralNetwork` to exclude the `device` object during pickling and reconstruct it upon unpickling:
  ```python
  def __getstate__(self):
      state = self.__dict__.copy()
      if "device" in state:
          del state["device"]
      return state

  def __setstate__(self, state):
      self.__dict__.update(state)
      self.device = torch.device(getattr(self, "_device_str", "cpu"))
  ```

## 6. Docker Volume Mapping in Worktrees
**Issue**: Code changes made in the git worktree were not reflected inside the running containers due to relative path mapping resolution issues or volume caching.
**Solution**:
- Initially used absolute paths for debug visibility.
- Final solution: Used correct relative paths in `docker-compose.yml` (`./api`, `./models`) and reached outside the worktree for shared libraries using `../../../../trader/crypto-analysis`.
- Used `docker compose -p online-training up -d --force-recreate` to ensure new volume definitions were applied.

## 7. Pydantic Model Validation Errors
**Issue**: `Failed to get status: "TrainingStatusResponse" object has no field "message"`. The API logic attempted to populate a field that wasn't defined in the response model.
**Solution**:
- Updated `api/src/routes/training.py` to include the `message` field in `TrainingStatusResponse`.

## 8. Development Environment Port Conflicts
**Issue**: Running multiple instances of the stack (main project and feature worktree) caused port conflicts for Postgres (5432) and Redis (6379).
**Solution**:
- Implemented port isolation in the worktree `docker-compose.yml`:
  - API: `8000` -> `8001`
  - Postgres: `5432` -> `5433`
  - Redis: `6379` -> `6380`
- Used `-p online-training` project name to isolate networks and container names.

---

## Final Verification Results
- **Success Rate**: 100% (BTC and ETH training runs successful).
- **Persistence**: Models correctly saved as `.joblib` in `./models/`.
- **API Response**: Status and Model List endpoints verified working with new schema.
