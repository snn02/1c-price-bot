# 1C Price Bot

Telegram bot for helping sales managers prepare commercial offers for 1C products.

The v1 target is a long polling Telegram bot that receives a free-form request,
uses an OpenRouter model to understand requested products, calls the external
`mcp-1c-price` MCP server for current 1C prices, and returns a commercial offer
as a Markdown file rendered from a template.

## Current Status

This repository currently contains the project skeleton and planning
documentation only. Bot implementation, dependencies, tests, and OpenSpec change
artifacts will be added in later steps.

## Planned Runtime

- Python + aiogram
- Telegram long polling
- OpenRouter-compatible LLM API
- External MCP server: `mcp-1c-price`
- SQLite for local state
- Jinja2 Markdown template for generated offers

## Documentation

- [Scope](docs/scope.md)
- [Architecture](docs/architecture.md)
- [Testing scenarios](docs/testing-scenarios.md)
- [Decision record: v1 shape](docs/decisions/0001-v1-shape.md)
