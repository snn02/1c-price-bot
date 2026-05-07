import os
from pathlib import Path

import pytest

from price_bot.common.exceptions import ConfigError


class TestSettings:
    REQUIRED = {
        "TELEGRAM_TOKEN": "tok",
        "OPENROUTER_API_KEY": "key",
        "MCP_SERVER_PATH": "/path/mcp",
    }

    def _make(self, env: dict):
        from price_bot.common.config import Settings
        return Settings()

    def test_all_required_vars_set_creates_settings(self, monkeypatch):
        for k, v in self.REQUIRED.items():
            monkeypatch.setenv(k, v)
        from price_bot.common.config import Settings
        s = Settings()
        assert s.telegram_token == "tok"
        assert s.openrouter_api_key == "key"
        assert s.mcp_server_path == "/path/mcp"

    def test_missing_telegram_token_raises_config_error(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        monkeypatch.setenv("MCP_SERVER_PATH", "/path/mcp")
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
        from price_bot.common.config import Settings
        with pytest.raises(ConfigError):
            Settings()

    def test_missing_openrouter_api_key_raises_config_error(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
        monkeypatch.setenv("MCP_SERVER_PATH", "/path/mcp")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        from price_bot.common.config import Settings
        with pytest.raises(ConfigError):
            Settings()

    def test_missing_mcp_server_path_raises_config_error(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        monkeypatch.delenv("MCP_SERVER_PATH", raising=False)
        from price_bot.common.config import Settings
        with pytest.raises(ConfigError):
            Settings()

    def test_default_data_dir_is_data(self, monkeypatch):
        for k, v in self.REQUIRED.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("DATA_DIR", raising=False)
        from price_bot.common.config import Settings
        s = Settings()
        assert s.data_dir == "data"

    def test_default_db_path_is_data_bot_db(self, monkeypatch):
        for k, v in self.REQUIRED.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("DATA_DIR", raising=False)
        from price_bot.common.config import Settings
        s = Settings()
        assert Path(s.db_path) == Path("data") / "bot.db"

    def test_custom_data_dir_changes_db_path(self, monkeypatch):
        for k, v in self.REQUIRED.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("DATA_DIR", "var/bot")
        from price_bot.common.config import Settings
        s = Settings()
        assert Path(s.db_path) == Path("var/bot") / "bot.db"

    def test_quote_template_path_derived_from_templates_dir(self, monkeypatch):
        for k, v in self.REQUIRED.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("TEMPLATES_DIR", "tpls")
        from price_bot.common.config import Settings
        s = Settings()
        assert Path(s.quote_template_path) == Path("tpls") / "quote.md.j2"
