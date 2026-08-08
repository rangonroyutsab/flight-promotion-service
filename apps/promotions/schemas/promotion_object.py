from pydantic import BaseModel


class PromotionObject(BaseModel):
    promotion_id: str
    title: str
    content: str


class DailyPromotionsOutput(BaseModel):
    date: str
    generated_at: str
    promotions: list[PromotionObject]
