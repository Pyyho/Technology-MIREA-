import uuid
import time
import hmac
import hashlib
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# Секретный ключ для подписей
SECRET_KEY = "your-secret-key-change-in-production"
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Простая база данных пользователей (для демонстрации)
users_db = {
    "user123": {
        "password": "password123",
        "user_id": str(uuid.uuid4()),
        "name": "Test User",
        "email": "user@example.com"
    }
}


def verify_credentials(username: str, password: str) -> bool:
    """Проверка учетных данных пользователя"""
    user = users_db.get(username)
    return user and user["password"] == password


def get_user_id(username: str) -> str:
    """Получение user_id по username"""
    return users_db.get(username, {}).get("user_id", "")


def get_user_profile(user_id: str) -> dict:
    """Получение профиля пользователя по user_id"""
    for username, data in users_db.items():
        if data["user_id"] == user_id:
            return {
                "username": username,
                "name": data["name"],
                "email": data["email"]
            }
    return None


# Задание 5.2 - Создание подписанной сессии
def create_signed_session(user_id: str) -> str:
    """Создание подписанной сессии"""
    return serializer.dumps({"user_id": user_id})


def verify_signed_session(token: str) -> str:
    """Проверка подписанной сессии"""
    try:
        data = serializer.loads(token, max_age=300)  # 5 минут
        return data["user_id"]
    except (BadSignature, SignatureExpired):
        return None


# Задание 5.3 - Сессия с временем активности
def create_session_with_activity(user_id: str) -> str:
    """Создание сессии с временем последней активности"""
    timestamp = int(time.time())
    data = f"{user_id}.{timestamp}"
    signature = hmac.new(
        SECRET_KEY.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{data}.{signature}"


def verify_session_with_activity(token: str) -> tuple:
    """Проверка сессии с временем активности"""
    try:
        user_id, timestamp, signature = token.split('.')
        timestamp = int(timestamp)

        # Проверка подписи
        expected_data = f"{user_id}.{timestamp}"
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            expected_data.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return None, None, "invalid"

        current_time = int(time.time())
        time_diff = current_time - timestamp

        # Проверка срока действия
        if time_diff > 300:  # больше 5 минут
            return None, None, "expired"

        return user_id, timestamp, time_diff
    except (ValueError, AttributeError):
        return None, None, "invalid"