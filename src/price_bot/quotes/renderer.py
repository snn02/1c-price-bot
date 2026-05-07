import os
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from price_bot.common.config import Settings
from price_bot.common.exceptions import BotError
from price_bot.common.types import QuoteDraft, QuoteItem


class Renderer:
    def __init__(self, settings: Settings) -> None:
        self._output_dir = settings.output_dir
        env = Environment(
            loader=FileSystemLoader(settings.templates_dir),
            autoescape=False,
        )
        try:
            self._template = env.get_template("quote.md.j2")
        except TemplateNotFound as exc:
            raise BotError(f"Quote template not found: {exc}") from exc

    def render(self, draft: QuoteDraft, items: list[QuoteItem]) -> str:
        selected = [i for i in items if i.status == "selected"]
        total_sum = sum(i.line_sum or 0 for i in selected)

        template_items = [
            {
                "code": i.selected_product_code or "",
                "name": i.selected_product_name or i.source_query,
                "qty": i.qty,
                "price_retail": round(i.price_retail or 0),
                "line_sum": round(i.line_sum or 0),
                "vat": i.vat or "",
            }
            for i in selected
        ]

        return self._template.render(
            client_name=draft.client_name or "",
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            items=template_items,
            total_sum=round(total_sum),
            note=None,
        )

    def save(self, content: str, draft_id: int) -> str:
        Path(self._output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"quote_{draft_id}_{timestamp}.md"
        path = os.path.join(self._output_dir, filename)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return os.path.abspath(path)
