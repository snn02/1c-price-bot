# Scope

## Goal

Build a first working version of a Telegram assistant that helps a sales manager
prepare a commercial offer for 1C products in the field.

The manager writes a free-form request in Telegram. The bot uses an OpenRouter
model to interpret the request, calls the `mcp-1c-price` MCP server to find
current 1C products and prices, asks clarifying questions when a product choice
is ambiguous, and returns the final commercial offer as a Markdown file.

## In Scope for v1

- Telegram bot launched via long polling.
- Free-form text requests from a sales manager.
- OpenRouter LLM integration with the model selected through environment
  configuration.
- MCP integration with `mcp-1c-price`.
- Calls to MCP tools:
  - `search_products`
  - `get_product`
  - `build_quote`
  - `refresh_prices`
- Local SQLite storage for users, messages, quote drafts, and selected items.
- Markdown commercial offer generation from a template.
- Sending the generated Markdown file back to the manager in Telegram.
- `/start` command with a short usage message.
- `/refresh_prices` command for updating the local 1C price database through MCP.

## Out of Scope for v1

- DOCX generation.
- Telegram webhook mode.
- CRM features.
- User roles and permissions.
- Admin UI.
- Multiple commercial offer templates.
- PostgreSQL or other external database services.
- Horizontal scaling or multi-instance deployment.
- Automatic synchronization with external sales systems.

## Success Criteria

- A manager can start the bot and understand the basic workflow.
- A manager can request a commercial offer in natural Russian text.
- The bot can identify requested product positions and quantities.
- The bot can use MCP price tools to build or validate the quote.
- The bot can ask for clarification when a product choice is ambiguous.
- The bot can generate and send a Markdown commercial offer file.
- Draft state survives a bot restart.
