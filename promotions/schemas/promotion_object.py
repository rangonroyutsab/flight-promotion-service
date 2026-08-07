from typing import Any, Dict, Literal
from pydantic import BaseModel


class PromotionContent(BaseModel):
    title: str
    content: str


class GenerationMeta(BaseModel):
    provider: str
    model: str
    generated_at: str


class PromotionObject(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    promotion_id: str
    promotion: PromotionContent
    flight: Dict[str, Any]
    generation: GenerationMeta
