from pydantic import BaseModel, Field
from typing import Any, Dict

class EventSchema(BaseModel):
    name: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
