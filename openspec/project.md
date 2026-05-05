# Project: 1C Price Bot

## Purpose

Build a Telegram assistant for sales managers who need current 1C product price
information and quick commercial offer preparation.

## v1 Direction

- Telegram long polling bot.
- OpenRouter LLM integration.
- External `mcp-1c-price` MCP server for price lookup and quote building.
- SQLite for local state.
- Markdown commercial offer generation from a template.

## Development Notes

- OpenSpec change artifacts and capability specs are intentionally not created
  yet.
- Create OpenSpec specifications only after an explicit command.
- Keep v1 focused on the smallest useful field workflow.
- Prefer clear module boundaries between Telegram, LLM, MCP, quote
  orchestration, storage, and rendering.
