from typing import Literal
from pydantic import BaseModel


class LatestPointer(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    date: str
    manifest_key: str
    updated_at: str
