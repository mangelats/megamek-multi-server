import asyncio
import logging
from typing import cast
from pydantic import RootModel
from quart import Quart, redirect, render_template, request, session, url_for, websocket
from quart_auth import QuartAuth, Unauthorized, current_user, login_required
from . import auth
from .servers import Command, Event
from .servers.extension import QuartMegaMek

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = Quart(__name__)
app.secret_key = "868051d50a154c19d7f284e74012056cbe957e045658df388c4554d85d57a8a6"
app.config['TEMPLATES_AUTO_RELOAD'] = True
QuartAuth(app)
QuartMegaMek(app)

@app.route('/')
@login_required
async def index() -> None:
    config_options=QuartMegaMek.config_options().model_dump()
    return await render_template(
        "index.html",
        name=current_user.auth_id,
        config_options=config_options,
    )

@app.websocket("/ws")
@login_required
async def ws() -> None:
    try:
        task = asyncio.ensure_future(_commands())
        events = QuartMegaMek.events()

        async for event in events:
            message = cast(Event, event).model_dump_json()
            await websocket.send(message)
    finally:
        task.cancel()
        await task

async def _commands() -> None:
    print("_commands")
    while True:
        try:
            message = await websocket.receive()
            print("received message", message)
            cmd = RootModel[Command].model_validate_json(message)
            print("command", cmd)
            await QuartMegaMek.apply_command(cmd.root)
        except Exception as e:
            print(e)
            raise e


@app.route('/login', methods=['GET', 'POST'])
async def login() -> None:
    error = None
    next = session.get('next')
    if request.method == 'POST':
        form = await request.form
        username = form['username']
        password = form['password']
        if user := auth.login(username, password):
            if next:
                del session['next']
            return redirect(next or '/')
        else:
            error = "Usuari o contrasenya incorrecte"

    return await render_template("login.html", error=error)

@app.errorhandler(Unauthorized)
async def redirect_to_login(*_) -> None:
    return redirect(url_for("login"))

@app.route('/logout')
async def logout() -> None:
    auth.logout()
    return redirect('/')
