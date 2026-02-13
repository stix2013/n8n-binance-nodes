# n8n File Write Permission Problem - Solution

**Date:** 2026-02-13  
**Problem:** n8n cannot write files to mounted host directory  
**Error:** `The file "/home/node/analyse/test.md" is not writable.`

---

## Problem Summary

When using n8n's **Read/Write Files from Disk** node to write files to a bind-mounted host directory, n8n throws a permission error even though the directory appears to have correct permissions inside the container.

### Error Messages Encountered

1. **Initial error:** `The file "/home/node/data/files/test.md" is not writable.`
2. **After path change:** `The file "/home/node/analyse/test.md" is not writable.`
3. **SELinux issues:** `Permission denied` on various paths

---

## Root Causes

### 1. Task Runners Execute File Operations

n8n uses **external task runners** (when `N8N_RUNNERS_ENABLED=true`) to execute workflow nodes. The Read/Write Files node is executed by the `task-runners` container, NOT the main `n8n` container.

**Key insight:** Volume mounts and environment variables must be configured on **BOTH** services.

### 2. SELinux with Bind Mounts

On systems with SELinux in enforcing mode:
- Bind-mounted directories appear as owned by `root:root` inside containers
- Standard Docker volume permissions don't work without proper SELinux labels
- The `:Z` or `:z` flags or directory permissions `777` are required

### 3. n8n File Access Restrictions

n8n has a security feature controlled by `N8N_RESTRICT_FILE_ACCESS_TO` that limits which directories can be accessed by file operations. This must be explicitly set to allow access to custom mount points.

### 4. Container User Mismatch

- n8n runs as user `node` (UID 1000)
- task-runners run as user `runner` (UID 1000)
- Both need write access to the mounted directory
- The parent directory ownership can block access even if subdirectory is world-writable

---

## Solution

### Final Working Configuration

#### 1. Host Directory Permissions

Make the host directory world-writable (required for SELinux systems):

```bash
chmod 777 ./docs/analyse
```

#### 2. docker-compose.yml Changes

**n8n service:**

```yaml
services:
  n8n:
    image: n8nio/n8n:${N8N_VERSION:-2.6.4-amd64}
    container_name: n8n-main
    restart: always
    user: "1000:1000"
    environment:
      # File access restriction - MUST include your mount path
      - N8N_RESTRICT_FILE_ACCESS_TO=/home/node/analyse
      # ... other env vars ...
    volumes:
      - n8n_data:/home/node/.n8n
      - n8n_mcp:/data/mcp
      - ./nodes/@stix/n8n-nodes-binance-kline:/home/node/.n8n/custom/node_modules/@stix/n8n-nodes-binance-kline
      - ./nodes/@stix/n8n-nodes-markdown-saver:/home/node/.n8n/custom/node_modules/@stix/n8n-nodes-markdown-saver
      # Mount your host directory to container
      - ./docs/analyse:/home/node/analyse:rw
```

**task-runners service:**

```yaml
  task-runners:
    image: n8nio-runners:${N8N_VERSION:-2.6.4}-local
    build:
      context: ./dockers
      dockerfile: Dockerfile
      args:
        - N8N_VERSION=${N8N_VERSION:-2.6.4}
    restart: always
    container_name: n8n-runners
    environment:
      - N8N_RUNNERS_TASK_BROKER_URI=http://n8n-main:5679
      # CRITICAL: Must also set file access restriction on task-runners!
      - N8N_RESTRICT_FILE_ACCESS_TO=/home/node/analyse
      - N8N_RUNNERS_AUTH_TOKEN=${N8N_RUNNERS_AUTH_TOKEN}
      # ... other env vars ...
    volumes:
      - ./config/n8n-task-runners.json:/etc/n8n-task-runners.json
      # CRITICAL: Must also mount the volume on task-runners!
      - ./docs/analyse:/home/node/analyse:rw
    depends_on:
      - n8n
```

### Key Configuration Points

| Setting | n8n Service | task-runners Service | Why |
|---------|-------------|---------------------|-----|
| `N8N_RESTRICT_FILE_ACCESS_TO` | ✅ Required | ✅ Required | Allows n8n to access the directory |
| Volume mount | ✅ Required | ✅ Required | Makes directory available in container |
| `user: "1000:1000"` | ✅ Keep it | ❌ Not needed | n8n needs explicit user, task-runners has it built-in |

---

## Testing

### Verify Container Access

Test the main n8n container:
```bash
docker compose exec n8n sh -c "touch /home/node/analyse/test.txt && echo 'n8n can write' && rm /home/node/analyse/test.txt"
```

Test the task-runners container:
```bash
docker compose exec task-runners sh -c "touch /home/node/analyse/test.txt && echo 'task-runners can write' && rm /home/node/analyse/test.txt"
```

### Verify Environment Variable

Check that `N8N_RESTRICT_FILE_ACCESS_TO` is set in task-runners:
```bash
docker compose exec task-runners sh -c "echo \$N8N_RESTRICT_FILE_ACCESS_TO"
# Should output: /home/node/analyse
```

---

## Path to Use in n8n Workflows

When configuring the **Read/Write Files from Disk** node:

- **File Path:** `/home/node/analyse/your-file-name.md`
- **Operation:** Write File to Disk
- **File Content:** Your content here

---

## Troubleshooting Checklist

If you still get permission errors:

1. ✅ Check host directory permissions: `ls -la docs/analyse`
2. ✅ Verify volume mount in BOTH n8n AND task-runners services
3. ✅ Verify `N8N_RESTRICT_FILE_ACCESS_TO` in BOTH services
4. ✅ Restart both containers: `docker compose up -d --force-recreate n8n task-runners`
5. ✅ Test write access manually in both containers
6. ✅ Check SELinux status: `getenforce` (if Enforcing, ensure directory is 777)

---

## References

- n8n File Access Documentation: https://docs.n8n.io/hosting/configuration/#file-access
- Docker Bind Mounts: https://docs.docker.com/storage/bind-mounts/
- SELinux and Docker: https://docs.docker.com/storage/bind-mounts/#configure-the-selinux-label
- Task Runners in n8n: https://docs.n8n.io/hosting/scaling/task-runners/

---

## Related Issues

- Integration testing architecture: See [2026-02-04-integration-testing-architecture.md](./2026-02-04-integration-testing-architecture.md)

---

## Environment

- **n8n Version:** 2.6.4-amd64
- **Docker Version:** 29.1.5
- **Host OS:** Linux with SELinux Enforcing
- **Configuration:** External task runners enabled
