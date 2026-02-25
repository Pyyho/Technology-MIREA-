from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


class UserBase(BaseModel):
    """Базовая модель пользователя"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: str = Field(..., description="Email пользователя")


class UserCreate(UserBase):
    """Модель для создания пользователя (с паролем)"""
    password: str = Field(..., min_length=6, description="Пароль")

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Пароль должен содержать минимум 6 символов')
        return v


class User(UserBase):
    """Модель пользователя с полными данными"""
    id: int
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    """Модель для обновления пользователя (PATCH)"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    is_active: Optional[bool] = None


class Message(BaseModel):
    """Модель сообщения"""
    id: Optional[int] = None
    user_id: int
    content: str = Field(..., min_length=1, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True


class MessageCreate(BaseModel):
    """Модель для создания сообщения"""
    content: str = Field(..., min_length=1, max_length=1000)


class MessageResponse(BaseModel):
    """Модель ответа с сообщением"""
    message: str
    user: User
    timestamp: datetime = Field(default_factory=datetime.now)