from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Dict, List, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeFloat,
    PositiveInt,
    field_validator,
    model_validator,
)

from pydantic_extra_types.color import Color
from src.agents.core.errors import GitValidationError
from src.agents.core.logger import get_logger
from src.agents.generators.banners import ascii
