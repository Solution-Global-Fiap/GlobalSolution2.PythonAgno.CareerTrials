from typing import Dict, List, Optional
from pydantic import BaseModel

class Challenge(BaseModel):
    title: str
    description: str
    type: str
    difficulty: str
    xp: int
    level: int
    estimatedTime: Optional[str] = None
    tags: Optional[List[str]] = []
    questions: Optional[List[Dict]] = []