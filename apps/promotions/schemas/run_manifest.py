from typing import Literal

from pydantic import BaseModel


class ManifestItem(BaseModel):
    promotion_id: str
    canonical_key: str | None = None
    status: str
    error: str | None = None


class RunManifest(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    date: str
    timezone: str
    status: str
    started_at: str
    finished_at: str
    selected_count: int
    succeeded_count: int
    failed_count: int
    output_key: str | None = None
    input_key: str | None = None
    items: list[ManifestItem]
