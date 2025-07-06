from flask import Request
import flask_login
from typing import Optional
from pwd_file import hashed_password
from werkzeug.security import check_password_hash

class User(flask_login.UserMixin):
    id: str

    @staticmethod
    def from_username(username: str) -> 'User':
        assert username, "Empty (invalid) username!"

        user = User()
        user.id = username
        return user

    @property
    def username(self) -> str:
        return self.id


def login(username: str, password: str) -> Optional[User]:
    password_hash = hashed_password(username)
    if password_hash is None:
        return
    if not check_password_hash(password_hash, password):
        return
    
    user = User.from_username(username)
    flask_login.login_user(user)
    return user

def logout() -> None:
    flask_login.logout_user()

current_user: User = flask_login.current_user

login_manager = flask_login.LoginManager()
login_manager.login_view = 'login'

@login_manager.user_loader
def user_loader(username: str) -> Optional[User]:
    return _load_user(username)

@login_manager.request_loader
def request_loader(request: Request) -> Optional[User]:
    username = request.form.get('username')
    if not username:
        return

    return _load_user(username)

def _load_user(username: str) -> Optional[User]:
    if not username:
        return

    password_hash = hashed_password(username)
    if password_hash is not None:
        return User.from_username(username)