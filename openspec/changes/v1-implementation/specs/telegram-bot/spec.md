## ADDED Requirements

### Requirement: Запуск бота через long polling
`price_bot.bot.main` SHALL инициализировать aiogram `Bot` и `Dispatcher`,
запускать MCP subprocess, инициализировать БД, затем запускать long polling.
При остановке (SIGINT/SIGTERM) MUST корректно завершать subprocess MCP.

#### Scenario: Успешный старт
- **WHEN** все переменные окружения заданы и MCP_SERVER_PATH валиден
- **THEN** бот запускается и начинает принимать сообщения

#### Scenario: Корректное завершение
- **WHEN** получен SIGINT
- **THEN** MCP subprocess завершается, бот останавливается без ошибок

---

### Requirement: Команда /start
Handler `/start` SHALL отвечать коротким сообщением на русском языке, объясняющим
как запросить КП (пример запроса, упоминание /refresh_prices).

#### Scenario: Ответ на /start
- **WHEN** пользователь отправляет /start
- **THEN** бот отвечает текстом с инструкцией и примером запроса

---

### Requirement: Команда /refresh_prices
Handler `/refresh_prices` SHALL вызывать `QuoteService.handle_refresh_prices()`,
который передаёт action `refresh_prices` в Quote service, и отправлять результат
менеджеру.

#### Scenario: Успешное обновление цен
- **WHEN** пользователь отправляет /refresh_prices
- **THEN** вызывается MCP refresh_prices и результат отправляется менеджером

#### Scenario: MCP недоступен
- **WHEN** MCP subprocess упал
- **THEN** бот отправляет понятное сообщение об ошибке

---

### Requirement: Обработка текстовых сообщений
Handler текстовых сообщений SHALL передавать сообщение в `QuoteService.handle_message`
и отправлять полученный текстовый ответ менеджеру.

#### Scenario: Продуктовый запрос
- **WHEN** менеджер отправляет "ERP, 10 лицензий"
- **THEN** Quote service обрабатывает сообщение и бот отвечает сводкой позиций

#### Scenario: Неизвестный запрос
- **WHEN** LLM не может разобрать намерение и возвращает malformed JSON
- **THEN** бот отвечает просьбой переформулировать запрос

---

### Requirement: Отправка Markdown КП как файла
Telegram handler SHALL отправлять результат через `bot.send_document` когда
`QuoteService.handle_message` возвращает путь к файлу (результат `create_quote_file`),
а не текстовый ответ.

#### Scenario: Отправка готового КП
- **WHEN** Quote service возвращает путь к `quote_42_....md`
- **THEN** файл отправляется менеджеру как документ в Telegram

---

### Requirement: Обработка необработанных ошибок
Если `QuoteService` выбрасывает необработанное исключение, Telegram handler SHALL
перехватывать его, логировать и отправлять менеджеру нейтральное сообщение об
ошибке без технических деталей.

#### Scenario: Неожиданная ошибка
- **WHEN** Quote service выбрасывает непредвиденное исключение
- **THEN** менеджер получает сообщение "Что-то пошло не так, попробуйте ещё раз"
