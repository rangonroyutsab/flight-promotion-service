from typing import Literal

from pydantic import BaseModel


class LatestPointer(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    date: str
    manifest_key: str
    output_key: str | None = None
    input_key: str | None = None
    updated_at: str
