import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "SimpleSecretKeyIsTryingToBeVeryBigYeah"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

bearer_scheme = HTTPBearer()

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    try:
        return decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Недействительный токен")


def require_dispatcher(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != 2:
        raise HTTPException(status_code=403, detail="Доступ только для диспетчера")
    return user


def require_courier(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != 1:
        raise HTTPException(status_code=403, detail="Доступ только для курьера")
    return user