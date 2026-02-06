from typing import ClassVar

from agents.config.settings import ConfigLoader
from agents.core.errors import UnsupportedServiceError
from agents.extractors.models import RepositoryContext
from agents.models.anthropic import AnthropicHandler
from agents.models.base import BaseModelHandler
from agents.models.enums import LLMProviders
from agents.models.gemini import GeminiHandler
from agents.models.offline import OfflineHandler
from agents.models.openai import OpenAIHandler


class ModelFactory:
    """
    Factory class for creating LLM API handler instances.
    """

    _model_map: ClassVar[dict] = {
        LLMProviders.ANTHROPIC: AnthropicHandler,
        LLMProviders.GEMINI.value: GeminiHandler,
        LLMProviders.OLLAMA.value: OpenAIHandler,
        LLMProviders.OPENAI.value: OpenAIHandler,
        LLMProviders.OFFLINE.value: OfflineHandler,
    }

    @staticmethod
    def get_backend(
        config: ConfigLoader, context: RepositoryContext
    ) -> BaseModelHandler:
        """Retrieves configured LLM API handler instance."""
        llm_service = ModelFactory._model_map.get(config.config.llm.api)

        if llm_service is None:
            raise UnsupportedServiceError(
                f"Unsupported LLM provider: {config.config.llm.api}"
            )

        return llm_service(config, context)
