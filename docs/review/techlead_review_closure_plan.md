# План закрытия `techlead_review_active.md`

## Summary

Закрыть ревью одним документационным проходом в 5 группах: LLM contract,
состояние черновиков, MCP contract, renderer/config/storage, DB/module cleanups.
Цель — сделать документацию decision-complete для последующего OpenSpec.

## Key Changes

- LLM contract: prompt/input contract, JSON response, envelope `action`,
  `arguments`, `reason`, поведение при malformed response.
- Dialog state: `clarification_kind`, обработка `clarify_answer`, переходы
  `quote_drafts.status`, детерминированный `title`.
- MCP contract: bot-side adapter contract, lifecycle subprocess over stdio,
  graceful failure без частичного изменения черновика.
- Renderer/config/storage: `templates/quote.md.j2`, config variables,
  `aiosqlite`, PRAGMA на соединении.
- DB/code cleanup: scenarios для `find_drafts`, `remove_item`, `replace_item`,
  FK к `telegram_users.id`, `vat` как display text, `file_format` check,
  описание пакетов.

## Assumptions

- `rules/*.md` остаются human-readable prompt context, не DSL.
- Реальный MCP response может отличаться; бот документирует bot-side adapter
  contract.
- В v1 нет tool calling, только JSON response от LLM.
- В v1 всё локально: Telegram long polling, SQLite, `aiosqlite`, MCP subprocess
  over stdio.
