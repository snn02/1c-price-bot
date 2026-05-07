## ADDED Requirements

### Requirement: Запуск MCP subprocess при старте
`McpClient` SHALL запускать `mcp-1c-price` как subprocess при создании экземпляра,
используя путь из `MCP_SERVER_PATH` и транспорт `stdio`. Если запуск не удался,
MUST выбрасываться `MCPError`. Клиент MUST хранить статус subprocess (живой/мёртвый).

#### Scenario: Успешный запуск
- **WHEN** `MCP_SERVER_PATH` указывает на валидный исполняемый файл
- **THEN** subprocess запускается и `McpClient` готов принимать вызовы

#### Scenario: Неверный путь к серверу
- **WHEN** `MCP_SERVER_PATH` указывает на несуществующий файл
- **THEN** при создании `McpClient` выбрасывается `MCPError`

---

### Requirement: Reconnect при следующем запросе
McpClient MUST пересоздавать subprocess перед следующим вызовом инструмента,
если предыдущий вызов завершился `MCPError` или subprocess завершился аварийно.

#### Scenario: Автовосстановление после ошибки
- **WHEN** предыдущий вызов вернул `MCPError` и subprocess мёртв
- **THEN** следующий вызов `search_products` сначала перезапускает subprocess, затем выполняет вызов

---

### Requirement: search_products
`McpClient.search_products(query, limit=10) → list[Product]` SHALL вызывать
MCP-инструмент `search_products` и маппить ответ на список `Product`.
При ошибке MCP MUST выбрасываться `MCPError` без изменения состояния черновика.

#### Scenario: Успешный поиск
- **WHEN** вызывается `search_products("ERP сервер", limit=5)`
- **THEN** возвращается список `Product` с полями code, name, price_retail, vat

#### Scenario: MCP вернул ошибку
- **WHEN** MCP-сервер недоступен или вернул ошибку
- **THEN** выбрасывается `MCPError`

---

### Requirement: get_product
`McpClient.get_product(code) → Product | None` SHALL вызывать MCP-инструмент
`get_product`. Если продукт не найден, MUST возвращаться `None`.

#### Scenario: Продукт найден
- **WHEN** вызывается `get_product("2900000000000")`
- **THEN** возвращается `Product` с корректными полями

#### Scenario: Продукт не найден
- **WHEN** код не существует в базе
- **THEN** возвращается `None`

---

### Requirement: build_quote
`McpClient.build_quote(items: list[dict]) → QuoteResult` SHALL вызывать
MCP-инструмент `build_quote` со списком `{code, qty}` и возвращать `QuoteResult`
с полями `items` (список с line_sum) и `total_sum`.

#### Scenario: Успешная сборка КП
- **WHEN** передаётся список с одним элементом `{"code": "123", "qty": 2}`
- **THEN** возвращается `QuoteResult` с `total_sum > 0` и `items[0].line_sum > 0`

---

### Requirement: refresh_prices
`McpClient.refresh_prices() → str` SHALL вызывать MCP-инструмент `refresh_prices`
и возвращать `message` из ответа адаптера для показа менеджеру.

#### Scenario: Успешное обновление
- **WHEN** вызывается `refresh_prices()`
- **THEN** возвращается строка-статус из MCP response

---

### Requirement: Атомарность при ошибке MCP
Quote service MUST NOT сохранять частично изменённый черновик при возникновении
`MCPError` во время обработки `add_items`, `replace_item` или `new_calculation`.
Черновик и позиции MUST остаться в состоянии до начала операции.

#### Scenario: Откат при MCPError во время add_items
- **WHEN** MCP падает в середине `add_items`
- **THEN** черновик и `quote_items` не изменены, менеджер получает сообщение об ошибке
