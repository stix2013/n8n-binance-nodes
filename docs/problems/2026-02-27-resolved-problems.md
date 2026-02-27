# Resolved Problems

## Problem 1: Queue Mode Architecture Complexity

**Issue**: Initial setup used queue mode with n8n-worker + redis, which added complexity and created connection issues when external task-runners tried to connect.

**Root Cause**: The n8n documentation states: "When using Queue mode, each n8n container (main and workers) needs to have its own task runner"

**Solution**: Simplified architecture by removing queue mode entirely:
- Removed n8n-worker service
- Removed redis service  
- Now running n8n-main + external task-runners only

---

## Problem 2: Task-Runners Healthcheck Wrong Port

**Issue**: Healthcheck for task-runners was failing because it used port 5679 (n8n main port) instead of 5680 (task-runners port).

```yaml
# Before (broken)
healthcheck:
  test: ["CMD", "wget", "-q", "-O-", "http://task-runners:5679/healthz"]

# After (fixed)
healthcheck:
  test: ["CMD", "sh", "-c", "wget -q -O- http://task-runners:5680/healthz || exit 1"]
```

**Solution**: Changed healthcheck to use port 5680.

---

## Problem 3: Deprecated OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS

**Issue**: Deprecation warning in n8n logs when queue mode was disabled.

**Root Cause**: The variable `OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS=true` is only applicable when queue mode is enabled.

**Solution**: Removed from env-example since we removed queue mode.

---

## Problem 4: YAML Anchor Creating Unexpected Service

**Issue**: An `x-shared` YAML anchor in docker-compose.yml was inadvertently creating a third service due to anchor reference issues.

**Solution**: Cleaned up the docker-compose.yml to remove the problematic anchor pattern.

---

## Problem 5: External Runners Not Registering

**Issue**: External task-runners were connecting to wrong broker when using workers.

**Solution**: After removing queue mode and simplifying to external runners only, runners now properly register with n8n-main.

---

## Problem 6: Task-Runners Connectivity

**Issue**: External runners need to connect to the correct broker address.

**Solution**: Set `N8N_RUNNERS_BROKER_LISTEN_ADDRESS=0.0.0.0` to ensure the broker binds to all interfaces, allowing external runners to connect.

---

## Summary

| Problem | Solution |
|---------|----------|
| Queue mode complexity | Removed n8n-worker + redis, simplified to external runners |
| Healthcheck wrong port | Changed 5679 → 5680 |
| Deprecated OFFLOAD setting | Removed from env config |
| YAML anchor issues | Cleaned up docker-compose.yml |
| Runner connection issues | Simplified architecture, proper broker bind address |
