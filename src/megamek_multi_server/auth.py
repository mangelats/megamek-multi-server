from typing import Optional

from quart_auth import AuthUser, login_user, logout_user
from werkzeug.security import check_password_hash

from .pwd_file import hashed_password


def login(username: str, password: str) -> Optional[AuthUser]:
    password_hash = hashed_password(username)
    if password_hash is None:
        return None
    if not check_password_hash(password_hash, password):
        return None
    
    user = AuthUser(username)
    login_user(user)
    return user

def logout() -> None:
    logout_user()
