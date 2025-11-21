from typing import List
from pydantic import BaseModel

from dtos.Challenge import Challenge


class ChallengesResponse(BaseModel):
    challenges: List[Challenge]
    total: int
    session_id: str