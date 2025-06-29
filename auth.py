from datetime import datetime, timedelta, timezone
import aiofiles
import jwt

from typing import Annotated, Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestFormStrict
from passlib.context import CryptContext
from pydantic import BaseModel
from jwt.exceptions import InvalidTokenError


SECRET_KEY = "40d193f3f97e1d85e7c82981403bbaf8c20d3a07656d3e2f4bcc3cd9d6254203"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(minutes=30)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



class User(BaseModel):
    username: str

class UserInDB(User):
    hashed_password: str

async def get_user(username: str) -> Optional[UserInDB]:
    async with aiofiles.open('secrets/passwords.txt', mode='r') as f:
        async for line in f:
            [u, hashed_password] = line.rstrip().rsplit(":", 1)
            if u == username:
                return UserInDB(username=username, hashed_password=hashed_password)


async def decode_token(token: str) -> Optional[UserInDB]:
    # This doesn't provide any security at all
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload:
            return await get_user(payload.get('username'))
    except InvalidTokenError:
        pass

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    user = await decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def login_inner(form_data: OAuth2PasswordRequestFormStrict):
    user = await get_user(form_data.username)
    if user and pwd_context.verify(form_data.password, user.hashed_password):
        to_encode: dict[str, Any] = { "username": user.username, "exp": datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE }
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    
async def login(form_data: OAuth2PasswordRequestFormStrict):
    result = await login_inner(form_data)
    if result:
        return result
    else:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

async def hash_password(password: str) -> str:
    return pwd_context.hash(password)
