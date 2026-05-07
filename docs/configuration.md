# Конфигурация

## Переменные окружения v1

Пример файла окружения хранится в `.env.example`.

- `TELEGRAM_TOKEN` — токен Telegram-бота.
- `OPENROUTER_API_KEY` — API key для OpenRouter-compatible LLM API.
- `OPENROUTER_MODEL` — модель OpenRouter.
- `MCP_SERVER_PATH` — путь к запускаемому `mcp-1c-price`.
- `DATA_DIR` — директория локальных данных, по умолчанию `data`.
- `OUTPUT_DIR` — директория генерируемых КП, по умолчанию `outputs`.
- `RULES_DIR` — директория runtime-правил, по умолчанию `rules`.
- `TEMPLATES_DIR` — директория Jinja2-шаблонов, по умолчанию `templates`.

## Производные пути

- SQLite база бота: `${DATA_DIR}/bot.db`.
- Markdown-шаблон КП: `${TEMPLATES_DIR}/quote.md.j2`.
- Сгенерированные Markdown КП записываются в `OUTPUT_DIR`.

## Правила

- Модель LLM не зашивается в код и читается из `OPENROUTER_MODEL`.
- MCP-сервер в v1 запускается ботом как subprocess через `MCP_SERVER_PATH`.
- Все директории должны создаваться приложением при запуске, если они
  отсутствуют.
