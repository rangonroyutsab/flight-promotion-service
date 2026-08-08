from typing import Any, Literal

from pydantic import BaseModel


class PromotionInputItem(BaseModel):
    promotion_id: str
    flight_id: str
    prompt_text: str
    flight: dict[str, Any]


class DailyPromotionsInput(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    date: str
    created_at: str
    inputs: list[PromotionInputItem]
