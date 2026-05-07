## 1. Инфраструктура проекта

- [ ] 1.1 Создать `pyproject.toml` с зависимостями: aiogram>=3, aiosqlite, jinja2, openai, python-dotenv
- [ ] 1.2 Добавить точку входа `[project.scripts] price-bot = "price_bot.bot.main:main"`
- [ ] 1.3 Создать `src/price_bot/py.typed` и проверить, что пакеты импортируются

## 2. Волна 1: common

- [ ] 2.1 Реализовать `price_bot.common.exceptions`: `BotError`, `ConfigError`, `StorageError`, `LLMError`, `MCPError`, `ValidationError`
- [ ] 2.2 Реализовать `price_bot.common.types`: dataclasses `Product`, `QuoteItem`, `QuoteDraft`, `QuoteResult`, `Message`, `Conversation`, `GeneratedQuote`
- [ ] 2.3 Реализовать `price_bot.common.config`: класс `Settings`, загрузка из env, производные пути, `ConfigError` при отсутствии обязательных переменных

## 3. Волна 2а: storage

- [ ] 3.1 Реализовать `price_bot.storage.db`: `get_connection(settings)` с PRAGMA и `init_db(conn)`; DDL по `docs/database.md`
- [ ] 3.2 Реализовать `price_bot.storage.repositories.users`: `UserRepository.get_or_create`
- [ ] 3.3 Реализовать `price_bot.storage.repositories.conversations`: `get_or_create`, `set_active_draft`, `get_active_draft_id`
- [ ] 3.4 Реализовать `price_bot.storage.repositories.messages`: `save`, `get_last_n`
- [ ] 3.5 Реализовать `price_bot.storage.repositories.drafts`: `create`, `get_by_id`, `get_active`, `update_status`, `list_active`, `find_by_query`
- [ ] 3.6 Реализовать `price_bot.storage.repositories.items`: `insert_selected`, `get_by_draft`, `set_removed`
- [ ] 3.7 Реализовать `price_bot.storage.repositories.generated_quotes`: `save`

## 4. Волна 2б: llm

- [ ] 4.1 Реализовать `price_bot.llm.rules`: `RulesLoader.load(rules_dir) → str`
- [ ] 4.2 Реализовать `price_bot.llm.context`: `build_context(draft, messages, current_message, rules_text) → list[dict]` — system + rules + draft state + history + message
- [ ] 4.3 Реализовать `price_bot.llm.client`: `LLMClient(settings)`, метод `select_action(context) → ActionResponse` через OpenRouter API с `response_format=json_object`
- [ ] 4.4 Реализовать парсинг и валидацию `ActionResponse`: проверка action из списка 10, валидация arguments, `LLMError` при malformed/unknown/invalid

## 5. Волна 2в: mcp

- [ ] 5.1 Реализовать `price_bot.mcp.client`: `McpClient(settings)`, запуск subprocess, отслеживание статуса, reconnect-логика
- [ ] 5.2 Реализовать метод `search_products(query, limit) → list[Product]` с маппингом ответа
- [ ] 5.3 Реализовать метод `get_product(code) → Product | None`
- [ ] 5.4 Реализовать метод `build_quote(items) → QuoteResult`
- [ ] 5.5 Реализовать метод `refresh_prices() → str`
- [ ] 5.6 Покрыть все методы обработкой `MCPError` и инвариантом атомарности

## 6. Волна 2г: renderer

- [ ] 6.1 Реализовать `price_bot.quotes.renderer`: `Renderer(settings)`, загрузка `quote.md.j2` из `TEMPLATES_DIR`
- [ ] 6.2 Реализовать метод `render(draft, items) → str`: рендеринг через Jinja2, только selected позиции, округление денег
- [ ] 6.3 Реализовать метод `save(content, draft_id) → str`: запись в `OUTPUT_DIR`, создание директории при отсутствии

## 7. Волна 3: quote-service

- [ ] 7.1 Реализовать `price_bot.quotes.service.QuoteService.__init__`: dependency injection (storage, llm_client, mcp_client, renderer, settings)
- [ ] 7.2 Реализовать `handle_message`: сохранение сообщения, вызов LLM, dispatch по action, сохранение ответа
- [ ] 7.3 Реализовать action `add_items`: создание черновика при необходимости, MCP поиск, сохранение selected/ambiguous позиций, clarification при неоднозначности
- [ ] 7.4 Реализовать action `remove_item`: поиск позиции по target, перевод в removed, уточнение при множественных совпадениях
- [ ] 7.5 Реализовать action `replace_item`: removed старой + add_items для replacement_text
- [ ] 7.6 Реализовать action `new_calculation`: superseded текущего черновика, создание нового, add_items
- [ ] 7.7 Реализовать action `create_quote_file`: проверка client_name, clarification при отсутствии, render+save, generated_quotes, статус generated, сброс active_draft
- [ ] 7.8 Реализовать action `clarify_answer`: dispatch по clarification_kind (client_name / product_choice / bundle_choice / generic), очистка clarification полей
- [ ] 7.9 Реализовать action `list_drafts`: чтение из storage, форматирование списка
- [ ] 7.10 Реализовать action `find_drafts`: поиск по query, форматирование
- [ ] 7.11 Реализовать action `open_draft`: проверка владения, set_active_draft, сводка позиций
- [ ] 7.12 Реализовать action `refresh_prices`: вызов McpClient.refresh_prices, возврат результата
- [ ] 7.13 Реализовать `handle_refresh_prices` для команды /refresh_prices

## 8. Волна 4: telegram-bot

- [ ] 8.1 Реализовать `price_bot.bot.main`: инициализация aiogram Bot/Dispatcher, запуск McpClient и init_db, long polling, graceful shutdown
- [ ] 8.2 Реализовать handler `/start`: ответ с инструкцией и примером запроса
- [ ] 8.3 Реализовать handler `/refresh_prices`: вызов `QuoteService.handle_refresh_prices`, ответ
- [ ] 8.4 Реализовать handler текстовых сообщений: вызов `QuoteService.handle_message`
- [ ] 8.5 Реализовать отправку Markdown-файла через `bot.send_document` когда результат — путь к файлу
- [ ] 8.6 Реализовать глобальный error handler: перехват необработанных исключений, нейтральный ответ менеджеру, логирование

## 9. Ручная приёмка

- [ ] 9.1 Пройти сценарий 1 (простой запрос КП) из `docs/testing-scenarios.md`
- [ ] 9.2 Пройти сценарий 2 (обновление цен)
- [ ] 9.3 Пройти сценарий 3 (неоднозначный продукт + уточнение)
- [ ] 9.4 Пройти сценарий 4 (генерация файла и проверка шаблона)
- [ ] 9.5 Пройти сценарий 5 (восстановление черновика после перезапуска)
- [ ] 9.6 Пройти сценарии 6–9 (правила лицензирования, бандлы, апгрейды, просмотр черновиков)
- [ ] 9.7 Пройти сценарий 10 (два КП в одном разговоре)
- [ ] 9.8 Пройти сценарий 11 (/start)
