import asyncio
import logging
from typing import cast

from pydantic import RootModel
from quart import Quart, redirect, render_template, request, session, url_for, websocket
from quart_auth import current_user, login_required, QuartAuth, Unauthorized

from . import auth
from .servers import Command, Event
from .servers.extension import QuartMegaMek

__all__ = ["app"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = Quart(__name__)
app.config.from_prefixed_env()
QuartAuth(app)
QuartMegaMek(app)


@app.route("/")
@login_required
async def index():
    config_options = QuartMegaMek.config_options().model_dump()
    return await render_template(
        "index.html",
        name=current_user.auth_id,
        config_options=config_options,
    )

@app.route("/admin")
@login_required
async def admin():
    config_options = QuartMegaMek.config_options().model_dump()
    return await render_template(
        "admin.html",
        name=current_user.auth_id,
        config_options=config_options,
    )


@app.websocket("/ws")
@login_required
async def ws() -> None:
    try:
        task = asyncio.ensure_future(_commands(current_user.auth_id))
        events = QuartMegaMek.events()

        async for event in events:
            message = cast(Event, event).model_dump_json()
            await websocket.send(message)
    finally:
        task.cancel()
        await task


async def _commands(auth_id) -> None:
    while True:
        try:
            message = await websocket.receive()
            cmd = RootModel[Command].model_validate_json(message)
            await QuartMegaMek.apply_command(cmd.root, auth_id)
        except Exception as e:
            print(e)
            raise e


@app.route("/login", methods=["GET", "POST"])
async def login():
    error = None
    next = session.get("next")
    if request.method == "POST":
        form = await request.form
        username = form["username"]
        password = form["password"]
        if user := auth.login(username, password):
            if next:
                del session["next"]
            return redirect(next or "/")
        else:
            error = "Usuari o contrasenya incorrecte"

    return await render_template("login.html", error=error)


@app.errorhandler(Unauthorized)
async def redirect_to_login(*_):
    return redirect(url_for("login"))


@app.route("/logout")
async def logout():
    auth.logout()
    return redirect("/")
