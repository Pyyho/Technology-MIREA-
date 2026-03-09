from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
import re


# Задание 3.1 - Модель UserCreate
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    age: Optional[int] = Field(None, ge=1, le=150, description="Возраст пользователя")
    is_subscribed: Optional[bool] = Field(False, description="Подписка на рассылку")


# Задание 5.5 - Модель CommonHeaders
class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias="User-Agent")
    accept_language: str = Field(..., alias="Accept-Language")

    @field_validator('accept_language')
    @classmethod
    def validate_accept_language(cls, v: str) -> str:
        # Простая проверка формата Accept-Language
        pattern = r'^[a-z]{2}(-[A-Z]{2})?(,[a-z]{2}(-[A-Z]{2})?;q=\d\.\d)*$|^[a-z]{2}(-[A-Z]{2})?(,[a-z]{2}(-[A-Z]{2})?)*$'
        if not re.match(pattern, v, re.IGNORECASE):
            raise ValueError('Неверный формат Accept-Language')
        return v

    class Config:
        populate_by_name = True