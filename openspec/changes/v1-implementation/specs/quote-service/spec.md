## ADDED Requirements

### Requirement: Оркестрация входящего сообщения
`QuoteService.handle_message` SHALL выполнять следующие шаги в порядке:
1. Сохранять входящее сообщение в `messages`.
2. Получать или создавать `conversation` и активный черновик.
3. Вызывать `LLMClient.select_action` с контекстом.
4. При `LLMError` (malformed/unknown/invalid) — сохранять ответ бота с просьбой уточнить и возвращать его.
5. Выполнять выбранное действие.
6. Сохранять ответ бота в `messages`.
7. Возвращать текстовый ответ для Telegram.

#### Scenario: Успешная обработка add_items
- **WHEN** менеджер пишет "УТ, 10 лицензий" и LLM возвращает `add_items`
- **THEN** создаётся черновик, вызывается MCP, позиции сохраняются, возвращается сводка

#### Scenario: LLM вернул malformed JSON
- **WHEN** LLM возвращает текст без JSON
- **THEN** черновик не изменяется, менеджер получает сообщение с просьбой переформулировать

---

### Requirement: action add_items
`add_items` SHALL при отсутствии активного черновика создавать новый со статусом
`collecting`, title = trim(items_text)[:120]. Затем вызывать MCP для поиска и
сборки позиций. Выбранные позиции сохраняются со статусом `selected`. При
неоднозначности продукта позиция сохраняется со статусом `ambiguous` и черновик
переходит в `needs_clarification` с заполненными `clarification_question` и
`clarification_kind = "product_choice"`.

#### Scenario: Однозначный продукт
- **WHEN** action = add_items, items_text = "ERP корп", MCP возвращает один продукт
- **THEN** позиция сохраняется со статусом `selected`, черновик остаётся `collecting`

#### Scenario: Неоднозначный продукт
- **WHEN** action = add_items, items_text = "ДО", MCP возвращает ПРОФ и КОРП варианты
- **THEN** позиция сохраняется со статусом `ambiguous`, черновик переходит в `needs_clarification`, `clarification_kind = "product_choice"`

---

### Requirement: action remove_item
`remove_item` SHALL находить позиции текущего черновика по `target` (LIKE по
`source_query`, `selected_product_name`, `selected_product_code`) и переводить их
в `status = "removed"`. Черновик переходит в `collecting`. Если совпадений нет —
сообщить менеджеру. Если несколько совпадений — задать уточнение.

#### Scenario: Успешное удаление
- **WHEN** action = remove_item, target = "ЗУП", в черновике есть позиция "1С:ЗУП"
- **THEN** позиция переходит в `removed`, черновик в `collecting`

#### Scenario: Позиция не найдена
- **WHEN** target = "ЗУП", позиций с таким именем нет
- **THEN** черновик не изменяется, менеджер получает сообщение об отсутствии позиции

---

### Requirement: action replace_item
`replace_item` SHALL переводить найденную позицию в `removed`, затем выполнять
`add_items` для `replacement_text` в рамках того же черновика.

#### Scenario: Успешная замена
- **WHEN** action = replace_item, target = "бухгалтерия", replacement_text = "базовая"
- **THEN** старая позиция переходит в `removed`, новая добавляется через MCP

---

### Requirement: action new_calculation
`new_calculation` SHALL переводить текущий активный черновик в `superseded`,
создавать новый черновик и выполнять `add_items` для `items_text`.

#### Scenario: Замена расчёта
- **WHEN** есть активный черновик draft_a, action = new_calculation
- **THEN** draft_a получает статус `superseded`, создаётся draft_b, выполняется add_items

---

### Requirement: action create_quote_file
`create_quote_file` SHALL проверять наличие `client_name`. Если он отсутствует
и не передан в arguments, переводить черновик в `needs_clarification` с
`clarification_kind = "client_name"` и спрашивать имя клиента. Если клиент
известен — переводить в `ready`, вызывать Renderer, сохранять в `generated_quotes`,
переводить черновик в `generated`, сбрасывать `active_quote_draft_id` в NULL.

#### Scenario: Клиент известен
- **WHEN** action = create_quote_file, arguments = {"client_name": "ООО Ромашка"}
- **THEN** КП формируется, черновик переходит в `generated`, active_quote_draft_id = NULL

#### Scenario: Клиент неизвестен
- **WHEN** action = create_quote_file, arguments = {}, client_name IS NULL
- **THEN** черновик переходит в `needs_clarification`, clarification_kind = "client_name"

---

### Requirement: action clarify_answer
`clarify_answer` SHALL читать `clarification_kind` из текущего черновика и
интерпретировать `answer` в соответствии с типом. При `client_name` — сохранять
имя клиента, очищать clarification поля и переходить в `ready`. При
`product_choice` или `bundle_choice` — находить ambiguous позицию, вызывать MCP
для выбранного варианта, переводить в `selected`, очищать clarification поля,
переходить в `collecting`. При `generic` — передавать ответ обратно в LLM для
интерпретации.

#### Scenario: Ответ на clarification_kind = client_name
- **WHEN** clarification_kind = "client_name", answer = "ООО Ромашка"
- **THEN** client_name сохраняется, clarification поля очищаются, статус = ready

#### Scenario: Ответ на clarification_kind = product_choice
- **WHEN** clarification_kind = "product_choice", answer = "КОРП"
- **THEN** ambiguous позиция обновляется через MCP до selected, статус черновика = collecting

---

### Requirement: action list_drafts
`list_drafts` SHALL возвращать список незавершённых черновиков текущего
пользователя (статусы: collecting, needs_clarification, ready) с подсчётом
selected/ambiguous/not_found позиций и total_sum. MCP NOT вызывается.

#### Scenario: Есть незавершённые черновики
- **WHEN** action = list_drafts, у пользователя 2 черновика
- **THEN** возвращается текстовый список с id, title, статусом и суммой

---

### Requirement: action find_drafts
`find_drafts` SHALL искать незавершённые черновики по подстроке query в
title/client_name/manager_note. MCP NOT вызывается.

#### Scenario: Поиск по тексту
- **WHEN** action = find_drafts, query = "ERP"
- **THEN** возвращаются черновики, содержащие "ERP" в title или client_name

---

### Requirement: action open_draft
`open_draft` SHALL проверять владение черновиком, связывать его с текущим
разговором через `active_quote_draft_id` и возвращать сводку позиций.

#### Scenario: Успешное открытие
- **WHEN** action = open_draft, draft_id принадлежит пользователю
- **THEN** conversations.active_quote_draft_id обновляется, возвращается сводка

#### Scenario: Чужой черновик
- **WHEN** action = open_draft, draft_id принадлежит другому пользователю
- **THEN** черновик не открывается, менеджер получает сообщение об ошибке

---

### Requirement: action refresh_prices
`refresh_prices` SHALL вызывать `McpClient.refresh_prices()` и возвращать
результат менеджеру.

#### Scenario: Успешное обновление через action
- **WHEN** action = refresh_prices
- **THEN** вызывается MCP refresh_prices, результат возвращается менеджеру
