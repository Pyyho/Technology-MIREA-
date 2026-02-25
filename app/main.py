from fastapi import FastAPI, HTTPException, status, Query, Path, Body
from typing import Optional, List
from datetime import datetime

from app.config import load_config, Config
from app.logger import logger
from app.models import (
    User, UserCreate, UserUpdate,
    Message, MessageCreate, MessageResponse
)

# Загружаем конфигурацию
config: Config = load_config()

# Создаем приложение FastAPI
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    debug=config.debug,
    description="Практическое занятие №2: Работа с конечными точками и параметрами"
)

# ----- Временное хранилище данных (фейковая БД) -----
fake_users_db = {
    1: {"id": 1, "username": "vasya", "email": "vasya@example.com", "is_active": True,
        "created_at": datetime.now()},
    2: {"id": 2, "username": "katya", "email": "katya@example.com", "is_active": True,
        "created_at": datetime.now()},
}

fake_messages_db = []
user_id_counter = 3
message_id_counter = 1


# ============== 1. ПАРАМЕТРЫ ПУТИ (PATH PARAMETERS) ==============

@app.get("/")
async def root():
    """Корневой эндпоинт - приветствие"""
    logger.info("Запрос к корневому эндпоинту")
    return {
        "message": "Привет, МИРЭА!",
        "app_name": config.app_name,
        "version": config.app_version,
        "topic": "Параметры пути, запроса и тела"
    }


@app.get("/users/{user_id}", response_model=User)
async def get_user_by_id(
        user_id: int = Path(..., title="ID пользователя", ge=1, description="Введите ID пользователя")
):
    """
    Получение пользователя по ID (ПАРАМЕТР ПУТИ)

    - **user_id**: ID пользователя (целое число, >= 1)
    """
    logger.info(f"Запрос пользователя с ID: {user_id}")

    if user_id not in fake_users_db:
        logger.error(f"Пользователь с ID {user_id} не найден")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )

    return fake_users_db[user_id]


@app.get("/users/by-username/{username}")
async def get_user_by_username(
        username: str = Path(..., title="Имя пользователя", min_length=3, max_length=50)
):
    """
    Получение пользователя по имени (ПАРАМЕТР ПУТИ)

    - **username**: имя пользователя (строка)
    """
    logger.info(f"Поиск пользователя с именем: {username}")

    for user in fake_users_db.values():
        if user["username"] == username:
            return user

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Пользователь с именем '{username}' не найден"
    )


@app.delete("/users/{user_id}")
async def delete_user(
        user_id: int = Path(..., title="ID пользователя для удаления", ge=1)
):
    """
    Удаление пользователя по ID (ПАРАМЕТР ПУТИ)

    - **user_id**: ID пользователя для удаления
    """
    logger.info(f"Попытка удаления пользователя с ID: {user_id}")

    if user_id not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )

    del fake_users_db[user_id]
    logger.info(f"Пользователь с ID {user_id} удален")

    return {"message": f"Пользователь с ID {user_id} успешно удален"}


# ============== 2. ПАРАМЕТРЫ ЗАПРОСА (QUERY PARAMETERS) ==============

@app.get("/users/", response_model=List[User])
async def get_users(
        limit: int = Query(10, title="Лимит", ge=1, le=100, description="Количество пользователей для вывода"),
        skip: int = Query(0, title="Пропустить", ge=0, description="Сколько пользователей пропустить"),
        active_only: bool = Query(False, title="Только активные", description="Фильтр по активности"),
        username_contains: Optional[str] = Query(None, min_length=1, description="Фильтр по части имени")
):
    """
    Получение списка пользователей с фильтрацией (ПАРАМЕТРЫ ЗАПРОСА)

    Параметры:
    - **limit**: сколько пользователей вернуть (по умолчанию 10)
    - **skip**: сколько пользователей пропустить (пагинация)
    - **active_only**: только активные пользователи
    - **username_contains**: фильтр по части имени
    """
    logger.info(f"Запрос списка пользователей: limit={limit}, skip={skip}, active_only={active_only}")

    # Преобразуем в список для фильтрации
    users_list = list(fake_users_db.values())

    # Фильтр по активности
    if active_only:
        users_list = [u for u in users_list if u["is_active"]]

    # Фильтр по имени
    if username_contains:
        users_list = [u for u in users_list if username_contains.lower() in u["username"].lower()]

    # Пагинация
    paginated_users = users_list[skip:skip + limit]

    logger.info(f"Найдено {len(paginated_users)} пользователей")
    return paginated_users


@app.get("/messages/", response_model=List[Message])
async def get_messages(
        user_id: Optional[int] = Query(None, title="ID пользователя", ge=1, description="Фильтр по пользователю"),
        limit: int = Query(20, title="Лимит", ge=1, le=100),
        sort_by_date: str = Query("desc", regex="^(asc|desc)$", description="Сортировка по дате")
):
    """
    Получение сообщений с фильтрацией (ПАРАМЕТРЫ ЗАПРОСА)

    - **user_id**: фильтр по ID пользователя
    - **limit**: количество сообщений
    - **sort_by_date**: сортировка (asc - по возрастанию, desc - по убыванию)
    """
    logger.info(f"Запрос сообщений: user_id={user_id}, limit={limit}, sort={sort_by_date}")

    messages = fake_messages_db.copy()

    # Фильтр по пользователю
    if user_id:
        messages = [m for m in messages if m["user_id"] == user_id]

    # Сортировка
    if sort_by_date == "desc":
        messages.sort(key=lambda x: x["created_at"], reverse=True)
    else:
        messages.sort(key=lambda x: x["created_at"])

    return messages[:limit]


# ============== 3. ПАРАМЕТРЫ ТЕЛА ЗАПРОСА (BODY PARAMETERS) ==============

@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
        user: UserCreate = Body(..., description="Данные для создания пользователя")
):
    """
    Создание нового пользователя (ПАРАМЕТРЫ ТЕЛА ЗАПРОСА)

    Ожидает JSON с полями:
    - **username**: имя пользователя (обязательно)
    - **email**: email (обязательно)
    - **password**: пароль (минимум 6 символов)
    """
    global user_id_counter

    logger.info(f"Создание пользователя: {user.username}")

    # Проверка уникальности email
    for existing_user in fake_users_db.values():
        if existing_user["email"] == user.email:
            logger.warning(f"Email {user.email} уже существует")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )

    # Создание нового пользователя
    new_user = {
        "id": user_id_counter,
        "username": user.username,
        "email": user.email,
        "is_active": True,
        "created_at": datetime.now()
    }

    fake_users_db[user_id_counter] = new_user
    user_id_counter += 1

    logger.info(f"Пользователь создан с ID: {new_user['id']}")
    return new_user


@app.post("/users/{user_id}/messages/", response_model=Message)
async def create_message_for_user(
        user_id: int = Path(..., title="ID пользователя", ge=1),
        message: MessageCreate = Body(..., description="Текст сообщения")
):
    """
    Создание сообщения для конкретного пользователя (ПАРАМЕТРЫ ПУТИ + ТЕЛА)

    - **user_id**: ID пользователя (в пути)
    - **content**: текст сообщения (в теле)
    """
    global message_id_counter

    logger.info(f"Создание сообщения для пользователя {user_id}")

    # Проверка существования пользователя
    if user_id not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )

    # Создание сообщения
    new_message = {
        "id": message_id_counter,
        "user_id": user_id,
        "content": message.content,
        "created_at": datetime.now()
    }

    fake_messages_db.append(new_message)
    message_id_counter += 1

    logger.info(f"Сообщение создано с ID: {new_message['id']}")
    return new_message


# ============== 4. ОБНОВЛЕНИЕ ДАННЫХ (PUT и PATCH) ==============

@app.put("/users/{user_id}", response_model=User)
async def update_user_full(
        user_id: int = Path(..., title="ID пользователя", ge=1),
        user_update: UserCreate = Body(..., description="Полные данные для обновления")
):
    """
    Полное обновление пользователя (PUT) - ЗАМЕНЯЕТ все поля

    Требует все поля модели UserCreate
    """
    logger.info(f"Полное обновление пользователя {user_id}")

    if user_id not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )

    # Обновляем пользователя
    fake_users_db[user_id]["username"] = user_update.username
    fake_users_db[user_id]["email"] = user_update.email
    # Пароль не храним в явном виде в демо

    logger.info(f"Пользователь {user_id} полностью обновлен")
    return fake_users_db[user_id]


@app.patch("/users/{user_id}", response_model=User)
async def update_user_partial(
        user_id: int = Path(..., title="ID пользователя", ge=1),
        user_update: UserUpdate = Body(..., description="Частичные данные для обновления")
):
    """
    Частичное обновление пользователя (PATCH) - обновляет только указанные поля

    Можно отправить только те поля, которые нужно изменить
    """
    logger.info(f"Частичное обновление пользователя {user_id}")

    if user_id not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )

    # Обновляем только переданные поля
    user_data = fake_users_db[user_id]

    if user_update.username is not None:
        user_data["username"] = user_update.username

    if user_update.email is not None:
        user_data["email"] = user_update.email

    if user_update.is_active is not None:
        user_data["is_active"] = user_update.is_active

    logger.info(f"Пользователь {user_id} частично обновлен")
    return user_data


# ============== 5. КОМБИНИРОВАННЫЙ ПРИМЕР ==============

@app.get("/search/")
async def search_users(
        # Параметры запроса
        q: str = Query(..., min_length=2, description="Поисковый запрос"),
        limit: int = Query(10, ge=1, le=50),
        include_inactive: bool = Query(False),
        # Параметры пути могут быть добавлены при необходимости
):
    """
    Поиск пользователей (комбинация параметров)

    - **q**: поисковый запрос (обязательный)
    - **limit**: лимит результатов
    - **include_inactive**: включать неактивных пользователей
    """
    logger.info(f"Поиск: q='{q}', limit={limit}, include_inactive={include_inactive}")

    results = []
    for user in fake_users_db.values():
        # Поиск по имени или email
        if q.lower() in user["username"].lower() or q.lower() in user["email"].lower():
            if include_inactive or user["is_active"]:
                results.append(user)

    return results[:limit]


# ============== 6. ИНФОРМАЦИОННЫЙ ЭНДПОИНТ ==============

@app.get("/info")
async def get_app_info():
    """Информация о приложении"""
    return {
        "app_name": config.app_name,
        "version": config.app_version,
        "debug_mode": config.debug,
        "database_url": config.database_url,
        "total_users": len(fake_users_db),
        "total_messages": len(fake_messages_db)
    }


# Для запуска напрямую
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug
    )