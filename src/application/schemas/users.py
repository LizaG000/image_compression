from uuid import UUID
from datetime import datetime
from src.application.schemas.common import BaseModel

class UserSchemas(BaseModel):
    id: UUID
    name: str
    age: int
    phone: int
    email: str
    password: str
    created_at: datetime
    updated_at: datetime

class CreateUserSchema(BaseModel):
    name: str
    age: int
    phone: int
    email: str
    password: str
