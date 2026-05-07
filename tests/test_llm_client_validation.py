import pytest

from price_bot.common.exceptions import LLMError
from price_bot.llm.client import parse_action_response, ActionResponse


class TestParseActionResponse:
    def test_valid_add_items(self):
        raw = '{"action": "add_items", "arguments": {"items_text": "ERP"}, "reason": "ok"}'
        result = parse_action_response(raw)
        assert isinstance(result, ActionResponse)
        assert result.action == "add_items"
        assert result.arguments == {"items_text": "ERP"}
        assert result.reason == "ok"

    def test_malformed_json_raises_llm_error(self):
        with pytest.raises(LLMError) as exc_info:
            parse_action_response("не JSON вообще")
        assert exc_info.value.code == "malformed_response"

    def test_unknown_action_raises_llm_error(self):
        raw = '{"action": "fly_to_moon", "arguments": {}, "reason": "x"}'
        with pytest.raises(LLMError) as exc_info:
            parse_action_response(raw)
        assert exc_info.value.code == "unknown_action"

    def test_missing_required_argument_raises_llm_error(self):
        raw = '{"action": "add_items", "arguments": {}, "reason": "x"}'
        with pytest.raises(LLMError) as exc_info:
            parse_action_response(raw)
        assert exc_info.value.code == "invalid_arguments"

    def test_action_with_no_required_args_passes(self):
        raw = '{"action": "list_drafts", "arguments": {}, "reason": "x"}'
        result = parse_action_response(raw)
        assert result.action == "list_drafts"

    def test_find_drafts_requires_query(self):
        raw = '{"action": "find_drafts", "arguments": {}, "reason": "x"}'
        with pytest.raises(LLMError) as exc_info:
            parse_action_response(raw)
        assert exc_info.value.code == "invalid_arguments"

    def test_open_draft_requires_draft_id(self):
        raw = '{"action": "open_draft", "arguments": {"draft_id": 5}, "reason": "x"}'
        result = parse_action_response(raw)
        assert result.arguments["draft_id"] == 5

    def test_missing_reason_defaults_to_empty_string(self):
        raw = '{"action": "refresh_prices", "arguments": {}}'
        result = parse_action_response(raw)
        assert result.reason == ""

    def test_all_ten_actions_are_accepted(self):
        actions_and_args = [
            ("list_drafts", {}),
            ("find_drafts", {"query": "ERP"}),
            ("open_draft", {"draft_id": 1}),
            ("add_items", {"items_text": "ERP"}),
            ("replace_item", {"target": "ЗУП", "replacement_text": "базовая"}),
            ("remove_item", {"target": "ЗУП"}),
            ("new_calculation", {"items_text": "УХ"}),
            ("create_quote_file", {}),
            ("refresh_prices", {}),
            ("clarify_answer", {"answer": "КОРП"}),
        ]
        import json
        for action, args in actions_and_args:
            raw = json.dumps({"action": action, "arguments": args, "reason": "x"})
            result = parse_action_response(raw)
            assert result.action == action
