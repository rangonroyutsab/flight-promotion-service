from typing import List, Literal, Optional
from pydantic import BaseModel


class ManifestItem(BaseModel):
    promotion_id: str
    canonical_key: Optional[str] = None
    status: str
    error: Optional[str] = None


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
    items: List[ManifestItem]
