# n8n Credentials Reference

> ⚠️ **Security Warning**: This file contains credential references only. Actual credentials are encrypted in the database.

## Active Credentials

| Name | Type | Description |
|------|------|-------------|
| Telegram account | telegramApi | Telegram Bot API credentials |
| Binance account | binanceApi | Binance API key/secret |
| Gemini Api Free | googlePalmApi | Google Gemini API |
| Postgres account | postgres | PostgreSQL database credentials |
| Ollama Free | ollamaApi | Ollama local LLM |

## Notes

- All credentials are stored encrypted in the n8n database (`credentials_entity` table)
- Credentials are encrypted using n8n's encryption key defined in `N8N_ENCRYPTION_KEY` env var
- To update credentials, edit them in n8n UI: Settings → Credentials

## Related Files

- `.env` - Environment configuration
- `docker-compose.yml` - Service orchestration
