from enum import Enum


class LLMAuthKeys(str, Enum):
    """
    LLM API service environment variable keys.
    """

    ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
    GOOGLE_API_KEY = "GOOGLE_API_KEY"
    OLLAMA_HOST = "OLLAMA_HOST"
    OPENAI_API_KEY = "OPENAI_API_KEY"


class LLMProviders(str, Enum):
    """
    LLM API services supported.
    """

    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    OPENAI = "openai"
    OFFLINE = "offline"


class OpenAIModels(str, Enum):
    """
    Enumerated list of supported OpenAI models.
    """

    GPT35_TURBO = "gpt-3.5-turbo"
    GPT4_TURBO = "gpt-4-turbo"
    GPT4O_MINI = "gpt-4o-mini"
    GPT4O = "gpt-4o"


class BaseURLs(str, Enum):
    """
    Enumerated list of supported API base URLs.
    """

    ANTHROPIC = "https://api.anthropic.com/"
    GEMINI = "https://generativelanguage.googleapis.com/"
    OLLAMA = "http://localhost:11434/"
    OPENAI = "https://api.openai.com/"