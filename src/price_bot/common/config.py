import os
from pathlib import Path

from dotenv import load_dotenv

from price_bot.common.exceptions import ConfigError

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.telegram_token = self._require("TELEGRAM_TOKEN")
        self.openrouter_api_key = self._require("OPENROUTER_API_KEY")
        self.mcp_server_path = self._require("MCP_SERVER_PATH")

        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
        self.data_dir = os.getenv("DATA_DIR", "data")
        self.output_dir = os.getenv("OUTPUT_DIR", "outputs")
        self.rules_dir = os.getenv("RULES_DIR", "rules")
        self.templates_dir = os.getenv("TEMPLATES_DIR", "templates")

        self.db_path = str(Path(self.data_dir) / "bot.db")
        self.quote_template_path = str(Path(self.templates_dir) / "quote.md.j2")

    @staticmethod
    def _require(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ConfigError(f"Required environment variable {name!r} is not set")
        return value
