# Decision 0001: v1 Shape

## Status

Accepted.

## Context

The first version should help a sales manager quickly prepare a commercial
offer for 1C products from Telegram. The system needs current price data from
the existing `mcp-1c-price` MCP server and an LLM to interpret free-form
manager requests.

The first iteration should minimize infrastructure and document-format
complexity while still preserving a useful end-to-end workflow.

## Decisions

- Use Python and aiogram for the Telegram bot.
- Use Telegram long polling for v1.
- Use OpenRouter through environment-based configuration.
- Do not hard-code the model in application code.
- Use the external `mcp-1c-price` MCP server instead of reimplementing price
  lookup.
- Store local state in SQLite.
- Generate Markdown commercial offers from a template.
- Defer DOCX generation until a later iteration.

## Consequences

- The bot can be launched locally or on a simple VPS without public HTTPS.
- The OpenRouter model can be changed by editing configuration only.
- SQLite keeps v1 deployment simple but is not intended for multi-instance
  scaling.
- Markdown is easy to inspect, test, and adapt before investing in DOCX
  formatting.
- A later DOCX implementation can reuse the same quote service and MCP
  integration if renderer boundaries stay clean.
