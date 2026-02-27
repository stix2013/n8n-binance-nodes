# n8n Behind Zrok Reverse Proxy

## Problem

When running n8n behind Zrok reverse proxy, two issues may appear in container logs:

1. **X-Forwarded-For Error**:
   ```
   ValidationError: The 'X-Forwarded-For' header is set but the Express 'trust proxy' setting is false
   ```

2. **Deprecation Warning**:
   ```
   (node:7) [DEP0060] DeprecationWarning: The 'util._extend' API is deprecated. Please use Object.assign() instead.
   ```

## Root Cause

1. **X-Forwarded-For**: Zrok sets the `X-Forwarded-For` header for client IP forwarding, but n8n's Express server doesn't trust proxies by default.

2. **util._extend**: This is a Node.js deprecation warning from n8n's dependency tree (likely axios), harmless but noisy.

## Solution

### Fix X-Forwarded-For Error

Add to `.env`:

```bash
N8N_PROXY_HOPS=1
```

This tells n8n there's 1 proxy hop, enabling Express to trust the `X-Forwarded-For` header.

### Optional: Suppress Deprecation Warning

If the deprecation warning is annoying, add to `.env`:

```bash
NODE_OPTIONS="--no-deprecation"
```

Note: This warning is harmless and can be safely ignored.

## Verification

```bash
docker compose down && docker compose up -d
docker compose logs -f n8n
```

Check that the X-Forwarded-For error no longer appears.
