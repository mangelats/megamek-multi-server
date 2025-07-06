from flask import Request
import flask_login
from typing import Optional
from pwd_file import hashed_passwords
from werkzeug.security import check_password_hash

hashes = {
    "test": "scrypt:32768:8:1$lWV55EaDMutmo8c7$aa5600942ddcda2ae2e1dedfad51618336fa7314b931b920e3fd680d5b3b9f98973b1f8b1761a60d5d560afc1da57b7c615d82b75c44cfc552c1e254e0290e56"
}

class User(flask_login.UserMixin):
    id: str

    @staticmethod
    def from_username(username: str) -> 'User':
        user = User()
        user.id = username
        return user

    @property
    def username(self) -> str:
        return self.id


def login(username: str, password: str) -> Optional[User]:
    hashes = hashed_passwords()
    if username not in hashes or not check_password_hash(hashes[username], password):
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
    if username not in hashed_passwords():
        return

    return User.from_username(username)

@login_manager.request_loader
def request_loader(request: Request) -> Optional[User]:
    username = request.form.get('username')
    if username not in hashed_passwords():
        return

    return User.from_username(username)
