import pytest

from price_bot.common.exceptions import (
    BotError,
    ConfigError,
    LLMError,
    MCPError,
    StorageError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_llm_error_caught_as_bot_error(self):
        with pytest.raises(BotError):
            raise LLMError("fail", code="malformed_response")

    def test_mcp_error_caught_as_bot_error(self):
        with pytest.raises(BotError):
            raise MCPError("mcp down")

    def test_storage_error_caught_as_bot_error(self):
        with pytest.raises(BotError):
            raise StorageError("db gone")

    def test_config_error_caught_as_bot_error(self):
        with pytest.raises(BotError):
            raise ConfigError("missing var")

    def test_validation_error_caught_as_bot_error(self):
        with pytest.raises(BotError):
            raise ValidationError("bad value")

    def test_llm_error_has_code_attribute(self):
        exc = LLMError("bad json", code="malformed_response")
        assert exc.code == "malformed_response"

    def test_llm_error_default_code_is_unknown(self):
        exc = LLMError("something")
        assert exc.code == "unknown"

    def test_specific_errors_not_interchangeable(self):
        with pytest.raises(MCPError):
            raise MCPError("mcp")
        with pytest.raises(LLMError):
            raise LLMError("llm")
