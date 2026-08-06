from pydantic import BaseModel
from typing import List, Dict, Any

class RunManifest(BaseModel):
    schema_version: str
    date: str
    timezone: str
    status: str
    started_at: str
    finished_at: str
    selected_count: int
    succeeded_count: int
    failed_count: int
    items: List[Dict[str, Any]]
