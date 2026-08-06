from pydantic import BaseModel

class LatestPointer(BaseModel):
    schema_version: str
    date: str
    manifest_key: str
    updated_at: str
