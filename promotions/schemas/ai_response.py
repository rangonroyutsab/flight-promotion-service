from pydantic import BaseModel

class AIResponse(BaseModel):
    title: str
    content: str
