import json
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI

from price_bot.common.config import Settings
from price_bot.common.exceptions import LLMError

SUPPORTED_ACTIONS = {
    "list_drafts",
    "find_drafts",
    "open_draft",
    "add_items",
    "replace_item",
    "remove_item",
    "new_calculation",
    "create_quote_file",
    "refresh_prices",
    "clarify_answer",
}

REQUIRED_ARGS: dict[str, list[str]] = {
    "list_drafts": [],
    "find_drafts": ["query"],
    "open_draft": ["draft_id"],
    "add_items": ["items_text"],
    "replace_item": ["target", "replacement_text"],
    "remove_item": ["target"],
    "new_calculation": ["items_text"],
    "create_quote_file": [],
    "refresh_prices": [],
    "clarify_answer": ["answer"],
}


@dataclass
class ActionResponse:
    action: str
    arguments: dict[str, Any]
    reason: str


def parse_action_response(raw: str) -> ActionResponse:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMError(f"Malformed JSON response: {exc}", code="malformed_response") from exc

    action = data.get("action")
    if action not in SUPPORTED_ACTIONS:
        raise LLMError(f"Unknown action: {action!r}", code="unknown_action")

    arguments = data.get("arguments", {})
    required = REQUIRED_ARGS.get(action, [])
    for field in required:
        if field not in arguments or arguments[field] is None:
            raise LLMError(
                f"Missing required argument {field!r} for action {action!r}",
                code="invalid_arguments",
            )

    return ActionResponse(
        action=action,
        arguments=arguments,
        reason=data.get("reason", ""),
    )


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self._model = settings.openrouter_model

    async def select_action(self, context: list[dict]) -> ActionResponse:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=context,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or ""
        return parse_action_response(raw)
