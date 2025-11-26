from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CredentialCreate(BaseModel):
    credential_name: str
    access_key: str
    secret_key: str

class CredentialResponse(BaseModel):
    id: int
    credential_name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
