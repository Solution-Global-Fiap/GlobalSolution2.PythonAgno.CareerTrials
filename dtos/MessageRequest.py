from pydantic import BaseModel, Field, field_validator

class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    
    @field_validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()