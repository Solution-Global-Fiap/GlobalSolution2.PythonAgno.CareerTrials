from pydantic import BaseModel

class MessageResponse(BaseModel):
    response: str
    session_id: str
    user_id: str
    is_complete: bool = False