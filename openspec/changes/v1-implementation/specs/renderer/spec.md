## ADDED Requirements

### Requirement: Загрузка Jinja2-шаблона
`Renderer` SHALL загружать шаблон `quote.md.j2` из `TEMPLATES_DIR` при
инициализации через `jinja2.Environment` с `FileSystemLoader`. Если файл шаблона
не найден, MUST выбрасываться `BotError` при старте.

#### Scenario: Шаблон найден
- **WHEN** файл `templates/quote.md.j2` существует
- **THEN** `Renderer` инициализируется без ошибок

#### Scenario: Шаблон не найден
- **WHEN** файл `templates/quote.md.j2` отсутствует
- **THEN** при создании `Renderer` выбрасывается `BotError`

---

### Requirement: Генерация Markdown КП
`Renderer.render(draft, items) → str` SHALL рендерить шаблон с контекстом:
`client_name`, `generated_at` (ISO datetime), `items` (список QuoteItem со
статусом `selected`), `total_sum` (сумма line_sum по selected позициям),
`note` (опционально). Денежные значения MUST округляться до целых без дробной части.

#### Scenario: Рендеринг с одной позицией
- **WHEN** draft.client_name = "ООО Ромашка", items = [QuoteItem(qty=2, price_retail=100000, line_sum=200000, vat="НДС 20%")]
- **THEN** возвращается строка Markdown с таблицей, итогом 200000 и клиентом "ООО Ромашка"

#### Scenario: Денежные значения без дробной части
- **WHEN** line_sum = 199999.99
- **THEN** в выводе отображается `200000`

#### Scenario: Только selected позиции
- **WHEN** черновик содержит 3 позиции: 2 selected и 1 removed
- **THEN** в КП попадают только 2 selected позиции

---

### Requirement: Запись файла в OUTPUT_DIR
`Renderer.save(content, draft_id) → str` SHALL записывать Markdown-содержимое
в файл `{OUTPUT_DIR}/quote_{draft_id}_{timestamp}.md` и возвращать абсолютный путь.
Директория `OUTPUT_DIR` MUST создаваться автоматически если отсутствует.

#### Scenario: Запись файла
- **WHEN** вызывается `save(content, draft_id=42)`
- **THEN** файл создаётся в OUTPUT_DIR, путь содержит `quote_42_`

#### Scenario: OUTPUT_DIR не существует
- **WHEN** директория OUTPUT_DIR отсутствует
- **THEN** директория создаётся и файл записывается успешно
