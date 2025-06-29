from typing import Annotated
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestFormStrict
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import auth

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request, user: Annotated[auth.User, Depends(auth.get_current_user)]):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"name": user.username }
    )

class Hash(BaseModel):
    password: str

@app.post("/hash")
async def hash(hash: Hash):
    return { "response": await auth.hash_password(hash.password) }

@app.post("/token")
async def token(form_data: Annotated[OAuth2PasswordRequestFormStrict, Depends()]):
    return await auth.login(form_data)