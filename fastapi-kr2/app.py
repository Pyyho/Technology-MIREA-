from fastapi import FastAPI, HTTPException, Request, Response, Depends, Header
from fastapi.responses import JSONResponse
import time
from datetime import datetime
from typing import Optional, List
import uuid

from models import UserCreate, CommonHeaders
from products import sample_products
from auth import (
    verify_credentials, get_user_id, get_user_profile,
    create_signed_session, verify_signed_session,
    create_session_with_activity, verify_session_with_activity,
    SECRET_KEY
)

app = FastAPI(title="Контрольная работа №2", version="1.0.0")


# ==================== Задание 3.1 ====================
@app.post("/create_user", response_model=UserCreate)
async def create_user(user: UserCreate):
    """
    Создание пользователя
    """
    return user


# ==================== Задание 3.2 ====================
@app.get("/product/{product_id}")
async def get_product(product_id: int):
    """
    Получение информации о продукте по ID
    """
    for product in sample_products:
        if product["product_id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Продукт не найден")


@app.get("/products/search")
async def search_products(
        keyword: str,
        category: Optional[str] = None,
        limit: int = 10
):
    """
    Поиск продуктов по ключевому слову и категории
    """
    results = []

    for product in sample_products:
        # Поиск по ключевому слову в названии (регистронезависимый)
        if keyword.lower() in product["name"].lower():
            # Фильтрация по категории, если указана
            if category and product["category"].lower() != category.lower():
                continue
            results.append(product)

    # Ограничение количества результатов
    return results[:limit]


# ==================== Задание 5.1 ====================
@app.post("/login")
async def login(
        response: Response,
        username: str,
        password: str
):
    """
    Вход в систему (базовая аутентификация)
    """
    if verify_credentials(username, password):
        # Создаем простой токен (для задания 5.1)
        session_token = str(uuid.uuid4())

        # Устанавливаем cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=300,  # 5 минут
            secure=False  # Для тестирования без HTTPS
        )
        return {"message": "Успешный вход"}

    raise HTTPException(status_code=401, detail="Неверные учетные данные")


@app.get("/user")
async def get_user(request: Request):
    """
    Защищенный маршрут для получения информации о пользователе
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Для простоты проверяем, что токен существует (в реальном приложении нужна проверка в БД)
    # Здесь мы просто возвращаем тестового пользователя
    return {
        "username": "user123",
        "name": "Test User",
        "email": "user@example.com"
    }


# ==================== Задание 5.2 ====================
@app.post("/login/v2")
async def login_v2(
        response: Response,
        username: str,
        password: str
):
    """
    Вход с подписанной сессией
    """
    if verify_credentials(username, password):
        user_id = get_user_id(username)
        session_token = create_signed_session(user_id)

        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=300,
            secure=False
        )
        return {"message": "Успешный вход"}

    raise HTTPException(status_code=401, detail="Неверные учетные данные")


@app.get("/profile")
async def get_profile(request: Request, response: Response):
    """
    Защищенный профиль с проверкой подписи
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = verify_signed_session(session_token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")

    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=401, detail="User not found")

    return profile


# ==================== Задание 5.3 ====================
@app.post("/login/v3")
async def login_v3(
        response: Response,
        username: str,
        password: str
):
    """
    Вход с сессией, отслеживающей активность
    """
    if verify_credentials(username, password):
        user_id = get_user_id(username)
        session_token = create_session_with_activity(user_id)

        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=300,
            secure=False
        )
        return {"message": "Успешный вход"}

    raise HTTPException(status_code=401, detail="Неверные учетные данные")


@app.get("/profile/v3")
async def get_profile_v3(request: Request, response: Response):
    """
    Защищенный профиль с проверкой активности сессии
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        response.status_code = 401
        return {"message": "Unauthorized"}

    user_id, last_activity, status = verify_session_with_activity(session_token)

    if status == "invalid":
        response.status_code = 401
        return {"message": "Invalid session"}

    if status == "expired":
        response.status_code = 401
        return {"message": "Session expired"}

    current_time = int(time.time())
    time_diff = current_time - last_activity

    # Проверяем нужно ли обновить сессию
    if 180 <= time_diff < 300:  # между 3 и 5 минутами
        new_token = create_session_with_activity(user_id)
        response.set_cookie(
            key="session_token",
            value=new_token,
            httponly=True,
            max_age=300,
            secure=False
        )
    elif time_diff >= 300:
        response.status_code = 401
        return {"message": "Session expired"}

    profile = get_user_profile(user_id)
    if not profile:
        response.status_code = 401
        return {"message": "User not found"}

    return profile


# ==================== Задание 5.4 ====================
@app.get("/headers")
async def get_headers(
        request: Request,
        user_agent: Optional[str] = Header(None, alias="User-Agent"),
        accept_language: Optional[str] = Header(None, alias="Accept-Language")
):
    """
    Получение информации из заголовков запроса
    """
    if not user_agent or not accept_language:
        raise HTTPException(
            status_code=400,
            detail="Отсутствуют обязательные заголовки"
        )

    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }


# ==================== Задание 5.5 ====================
@app.get("/headers/v2")
async def get_headers_v2(headers: CommonHeaders = Depends()):
    """
    Получение заголовков с использованием Pydantic модели
    """
    return {
        "User-Agent": headers.user_agent,
        "Accept-Language": headers.accept_language
    }


@app.get("/info")
async def get_info(
        response: Response,
        headers: CommonHeaders = Depends()
):
    """
    Получение информации о пользователе с дополнительными данными
    """
    # Добавляем серверное время в заголовок
    response.headers["X-Server-Time"] = datetime.now().isoformat()

    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": headers.user_agent,
            "Accept-Language": headers.accept_language
        }
    }


# ==================== Запуск приложения ====================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)