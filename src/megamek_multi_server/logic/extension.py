import json
import os
from collections.abc import AsyncGenerator
from enum import Enum
from pathlib import Path
from typing import Optional

import aiofiles
from aiofiles.tempfile import TemporaryDirectory
from pydantic import BaseModel, RootModel
from quart import current_app, Quart

from megamek_multi_server.logic.server_description import ServerDescription

from .auth import FileAuth
from .commands import Command, CreateServer, DestroyServer
from .conductor import Conductor
from .config import Config
from .events import Event

_EXT_CODE = "QUART_MEGAMEK"
_CONFIG_KEY = "MEGAMEK_MULTI_SERVER"


class _ConductorState(str, Enum):
    ready = "ready"
    starting = "starting"
    closed = "closed"


class QuartMegaMek:
    _conductor: Conductor | _ConductorState
    _config: Config | None
    _file_auth: FileAuth | None

    def __init__(self, app: Optional[Quart] = None) -> None:
        self._conductor = _ConductorState.ready
        self._file_auth = None
        self._config_file = None
        self._config = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Quart) -> None:
        if _EXT_CODE in app.extensions:
            raise Exception("MegaMek extension has already been initialized")
        app.extensions[_EXT_CODE] = self

        config_file = app.config.get(_CONFIG_KEY)
        if config_file is None:
            raise Exception(f"No config file configured. Please set QUART_{_CONFIG_KEY} in env")

        with open(config_file, mode="r") as f:
            config = json.load(f)

        self._config = Config.model_validate(config)
        self._file_auth = FileAuth(self._config.passwords)

        if self._conductor == _ConductorState.ready:
            self._conductor = _ConductorState.starting
            app.while_serving(self._run_conductor)
        else:
            raise Exception("A conductor is already working")

    async def _run_conductor(self) -> AsyncGenerator[None, None]:
        assert self._config is not None
        async with TemporaryDirectory() as temp_dir:
            self._conductor = Conductor(Path(temp_dir), self._config.servers)
            yield
            await self._conductor.shutdown()
            self._conductor = _ConductorState.closed

    @staticmethod
    def current() -> "QuartMegaMek":
        return current_app.extensions[_EXT_CODE]

    @staticmethod
    def auth() -> FileAuth:
        auth = QuartMegaMek.current()._file_auth
        if auth is None:
            raise Exception("Extension not yet initialized")
        return auth

    @staticmethod
    def _current_conductor() -> Conductor:
        conductor = QuartMegaMek.current()._conductor
        if isinstance(conductor, _ConductorState):
            raise Exception("The conductor is not available")
        return conductor

    @staticmethod
    def config_options() -> "ConfigOptions":
        current = QuartMegaMek._current_conductor()
        return ConfigOptions(current.server_descriptions())

    @staticmethod
    def events() -> AsyncGenerator[Event, None]:
        return QuartMegaMek._current_conductor().events()

    @staticmethod
    async def apply_command(command: Command, auth_id: Optional[str]) -> None:
        if isinstance(command, CreateServer):
            await QuartMegaMek._current_conductor().start_server(
                command.server, command.id, auth_id
            )
        elif isinstance(command, DestroyServer):
            await QuartMegaMek._current_conductor().stop_server(command.id)


ConfigOptions = RootModel[list[str]]
