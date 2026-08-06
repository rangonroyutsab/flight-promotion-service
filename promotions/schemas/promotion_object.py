from pydantic import BaseModel
from typing import Dict, Any

class PromotionObject(BaseModel):
    schema_version: str
    promotion_id: str
    promotion: Dict[str, str]
    flight: Dict[str, Any]
    generation: Dict[str, str]
