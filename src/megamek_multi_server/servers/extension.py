import json
import os
from collections.abc import AsyncGenerator
from enum import Enum
from pathlib import Path
from typing import Optional

import aiofiles
from aiofiles.tempfile import TemporaryDirectory
from megamek_multi_server.servers.server_description import ServerDescription
from pydantic import BaseModel, RootModel
from quart import current_app, Quart

from .commands import Command, CreateServer, DestroyServer
from .conductor import AvailableServerDescriptions, Conductor
from .events import Event

_EXT_CODE = "QUART_MEGAMEK"


class _ConductorState(str, Enum):
    ready = "ready"
    starting = "starting"
    closed = "closed"


class QuartMegaMek:
    _conductor: Conductor | _ConductorState

    def __init__(self, app: Optional[Quart] = None) -> None:
        self._conductor = _ConductorState.ready
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Quart) -> None:
        if _EXT_CODE in app.extensions:
            raise Exception("MegaMek extension has already been initialized")
        app.extensions[_EXT_CODE] = self

        if self._conductor == _ConductorState.ready:
            self._conductor = _ConductorState.starting
            app.while_serving(self._run_conductor)
        else:
            raise Exception("A conductor is already working")

    async def _run_conductor(self) -> AsyncGenerator[None, None]:
        servers_file = os.environ["MEGAMEK_MULTI_SERVER_SERVERS"]
        async with aiofiles.open(servers_file, mode="r") as f:
            s: str = await f.read()
            servers = AvailableServerDescriptions(json.loads(s))
            async with TemporaryDirectory() as temp_dir:
                self._conductor = Conductor(Path(temp_dir), servers)
                yield
                await self._conductor.shutdown()
                self._conductor = _ConductorState.closed

    @staticmethod
    def current() -> "QuartMegaMek":
        return current_app.extensions[_EXT_CODE]

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
            await QuartMegaMek._current_conductor().start_server(command.server, command.id, auth_id)
        elif isinstance(command, DestroyServer):
            await QuartMegaMek._current_conductor().stop_server(command.id)

ConfigOptions = RootModel[list[str]]
