from typing import List, Optional
from pydantic import BaseModel

class Challenge(BaseModel):
    id: int | None = None
    title: str
    description: str
    type: str
    difficulty: str
    xp: int
    level: int
    estimatedTime: Optional[str] = None
    tags: Optional[List[str]] = []
    questions: list["Question"] | None = []

class Question(BaseModel):
    id: int | None = None
    question: str
    choices: list[str]
    answer: str