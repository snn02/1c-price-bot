## ADDED Requirements

### Requirement: Сборка LLM input context
Метод `build_context` SHALL формировать список сообщений в формате OpenAI chat
completions в следующем порядке:
1. `system` — роль бота, запрет придумывать продукты/цены, требование JSON response,
   затем содержимое всех Markdown-файлов из `RULES_DIR`.
2. `user`/`assistant` чередование из последних 10 сообщений разговора.
3. Компактная сериализация активного черновика как `system` или в system prompt.
4. Текущее сообщение менеджера как финальный `user`.

LLM MUST NOT получать полный прайс. Черновик сериализуется только если он активен.

#### Scenario: Сборка контекста с активным черновиком
- **WHEN** есть активный черновик и 3 сообщения истории
- **THEN** контекст содержит system instructions, rules, сериализованный черновик, 3 сообщения истории и текущее сообщение

#### Scenario: Сборка контекста без черновика
- **WHEN** активного черновика нет
- **THEN** контекст содержит system instructions, rules и текущее сообщение без draft state

#### Scenario: История ограничена 10 сообщениями
- **WHEN** разговор содержит 25 сообщений
- **THEN** в контекст попадают только последние 10

---

### Requirement: Вызов OpenRouter API и парсинг action response
`LLMClient.select_action(context) → ActionResponse` SHALL отправлять запрос к
OpenRouter с `response_format={"type": "json_object"}` и парсить JSON из текста
ответа. Результат MUST содержать поля `action`, `arguments`, `reason`.
`action` MUST входить в список из 10 поддерживаемых действий. `arguments` MUST
соответствовать схеме для данного action.

#### Scenario: Успешный парсинг валидного ответа
- **WHEN** модель возвращает `{"action": "add_items", "arguments": {"items_text": "ERP"}, "reason": "..."}`
- **THEN** возвращается `ActionResponse(action="add_items", arguments={"items_text": "ERP"}, reason="...")`

#### Scenario: Ответ не является валидным JSON
- **WHEN** модель возвращает произвольный текст без JSON
- **THEN** выбрасывается `LLMError` с кодом `malformed_response`

#### Scenario: JSON содержит неизвестный action
- **WHEN** модель возвращает `{"action": "unknown_action", "arguments": {}, "reason": "..."}`
- **THEN** выбрасывается `LLMError` с кодом `unknown_action`

#### Scenario: JSON содержит action без обязательных arguments
- **WHEN** модель возвращает `{"action": "add_items", "arguments": {}, "reason": "..."}`
- **THEN** выбрасывается `LLMError` с кодом `invalid_arguments`

---

### Requirement: Загрузка runtime-правил
`RulesLoader.load(rules_dir) → str` SHALL читать все `.md`-файлы из `RULES_DIR`
в алфавитном порядке и возвращать их конкатенацию. Если директория пустая или
отсутствует, MUST возвращаться пустая строка без ошибки.

#### Scenario: Загрузка правил из директории
- **WHEN** в `rules/` есть файлы `bundles.md`, `licensing.md`
- **THEN** возвращается конкатенация содержимого обоих файлов

#### Scenario: Пустая директория правил
- **WHEN** директория `rules/` существует, но пустая
- **THEN** возвращается пустая строка без ошибки
