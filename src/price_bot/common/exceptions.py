class BotError(Exception):
    pass


class ConfigError(BotError):
    pass


class StorageError(BotError):
    pass


class LLMError(BotError):
    def __init__(self, message: str, code: str = "unknown"):
        super().__init__(message)
        self.code = code


class MCPError(BotError):
    pass


class ValidationError(BotError):
    pass
