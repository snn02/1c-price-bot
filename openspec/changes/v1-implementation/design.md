## Context

Проект имеет полную проектную документацию (архитектура, схема БД, MCP-контракт,
конфигурация, шаблон КП, сценарии тестирования) и пустые пакеты-заглушки.
Реализация отсутствует. Все технические решения уже приняты и зафиксированы в
`docs/decisions/`.

## Goals / Non-Goals

**Goals:**
- Реализовать все слои v1 так, чтобы бот запускался и проходил 11 ручных сценариев из `docs/testing-scenarios.md`.
- Сохранить чёткие границы между пакетами: `common → storage/llm/mcp/renderer → quotes → bot`.
- Не вводить ничего за пределами v1 scope.

**Non-Goals:**
- DOCX, webhook, роли, мультиинстанс, CRM, внешние БД.
- Автоматические тесты в v1 (только ручная приёмка).
- Строгий DSL или rule engine для `rules/`.

## Decisions

### D1: Порядок реализации — волновой

Зависимости между пакетами диктуют порядок:

```
Волна 1:  common          (config, types, exceptions)
Волна 2:  storage  llm  mcp  renderer   (независимы между собой)
Волна 3:  quotes         (зависит от storage, llm, mcp, renderer)
Волна 4:  bot            (зависит от quotes)
```

Альтернатива «всё сразу» неработоспособна: `quotes` не скомпилируется без типов из `common` и контрактов из `storage`.

### D2: Общие типы данных — dataclasses в `common`

Все межпакетные типы (`Product`, `QuoteDraft`, `QuoteItem`, `QuoteResult` и др.)
определяются в `price_bot.common.types`. Пакеты импортируют типы оттуда, а не
определяют собственные.

Альтернатива TypedDict отклонена: dataclasses дают `__repr__`, валидацию через
`__post_init__` и IDE-автодополнение без накладных расходов.

### D3: aiosqlite + явный connection pool через контекстный менеджер

Каждый репозиторий получает `aiosqlite.Connection` через dependency injection
(передаётся из unit of work). PRAGMA включаются один раз при открытии соединения.

Альтернатива SQLAlchemy async отклонена: избыточна для single-instance SQLite v1.

### D4: LLM action selection — JSON в тексте ответа, не tool calling

Зафиксировано в `docs/architecture.md`. OpenRouter поддерживает tool calling,
но в v1 используется `json_object` response format для простоты и переносимости
между моделями.

### D5: MCP subprocess — запуск при старте, reconnect при ошибке

`McpClient` запускает subprocess в `bot/main.py` при старте и хранит ссылку.
При `MCPError` во время запроса клиент помечает subprocess как мёртвый; следующий
вызов пересоздаёт его. Частичные изменения черновика при ошибке MCP не сохраняются.

### D6: pyproject.toml — минимальный набор зависимостей

```
aiogram>=3.x
aiosqlite
jinja2
openai   # совместимый клиент для OpenRouter
```

`openai` SDK используется только как HTTP-клиент к OpenRouter-совместимому API;
anthropic SDK не нужен.

## Risks / Trade-offs

- **LLM возвращает невалидный JSON** → Quote service перехватывает `json.JSONDecodeError`, не меняет черновик, просит уточнение. Покрыто инвариантом.
- **MCP subprocess падает** → reconnect на следующем запросе; текущий запрос возвращает ошибку менеджеру.
- **Длинная история сообщений** → LLM input ограничен последними 10 сообщениями (зафиксировано в архитектуре).
- **SQLite при конкурентных запросах** → v1 single-instance, `busy_timeout = 5000` снижает вероятность конфликтов.

## Migration Plan

Первое развёртывание: БД создаётся при старте функцией `init_db()`. Миграций нет.
Запуск: `python -m price_bot.bot`.

## Open Questions

— Все технические вопросы закрыты документацией.
