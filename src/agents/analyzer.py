import asyncio
import time
from pathlib import Path
from typing import List, Tuple

from opentelemetry import trace
from pydantic import BaseModel, Field
from pydantic_ai import Agent, UnexpectedModelBehavior
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

import config
from utils import Logger, PromptManager, create_retrying_client

from .tools import FileReadTool, ListFilesTool


class AnalyzerAgentConfig(BaseModel):
    repo_path: Path = Field(..., description="The path to the repository")
    exclude_code_structure: bool = Field(default=False, description="Exclude code structure analysis")
    exclude_data_flow: bool = Field(default=False, description="Exclude data flow analysis")
    exclude_dependencies: bool = Field(default=False, description="Exclude dependencies analysis")
    exclude_request_flow: bool = Field(default=False, description="Exclude request flow analysis")
    exclude_api_analysis: bool = Field(default=False, description="Exclude api analysis")

