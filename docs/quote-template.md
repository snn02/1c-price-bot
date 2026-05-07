# Шаблон Markdown КП

## Файл

Runtime-шаблон v1 хранится в:

```text
templates/quote.md.j2
```

Renderer загружает этот Jinja2-шаблон из `TEMPLATES_DIR` и записывает
сформированное КП в `OUTPUT_DIR`.

## Данные шаблона

Шаблон ожидает:

- `client_name`
- `generated_at`
- `items`
- `total_sum`
- `note`

Каждый элемент `items` содержит:

- `code`
- `name`
- `qty`
- `price_retail`
- `line_sum`
- `vat`

## Форматирование

- Денежные значения выводятся округлёнными до целых значений.
- `vat` выводится как display text из MCP.
- Если `client_name` отсутствует, Quote service должен запросить его до
  генерации КП.
