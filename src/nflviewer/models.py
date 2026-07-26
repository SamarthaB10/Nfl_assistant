from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class APIModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class HealthResponse(APIModel):
    status: Literal["ok"] = "ok"
    data_loaded: bool
    supported_season: Literal[2025] = 2025
    formula_version: Literal["record-watchability-v1"] = "record-watchability-v1"

