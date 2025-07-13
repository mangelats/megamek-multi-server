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

from .commands import Command, CreateServer, DestroyServer
from .conductor import Conductor, ConductorConfig, Version
from .events import Event

_EXT_CODE = "QUART_MEGA_MECH"


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
            raise Exception("MegaMech extension has already been initialized")
        app.extensions[_EXT_CODE] = self

        if self._conductor == _ConductorState.ready:
            self._conductor = _ConductorState.starting
            app.while_serving(self._run_conductor)
        else:
            raise Exception("A conductor is already working")

    async def _run_conductor(self) -> AsyncGenerator[None, None]:
        config_file = os.environ["MEGAMEK_MULTI_SERVER_CONFIG"]
        async with aiofiles.open(config_file, mode="r") as f:
            s: str = await f.read()
            config = json.loads(s)
            async with TemporaryDirectory() as temp_dir:
                server_configs = ConductorConfig(config["available_configs"])
                self._conductor = Conductor(Path(temp_dir), server_configs)
                yield
                await self._conductor.stop_all_servers()
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
        result: dict[Version, ConfigVersionOption] = {}
        for k, v in QuartMegaMek._current_conductor().config.items():
            result[k] = ConfigVersionOption(
                mm_version=v.mm_version,
                mmconf=list(v.mmconf.keys()),
                mechs=list(v.mechs.keys()),
                maps=list(v.maps.keys()),
            )
        return ConfigOptions(result)

    @staticmethod
    def events() -> AsyncGenerator[Event, None]:
        return QuartMegaMek._current_conductor().events()

    @staticmethod
    async def apply_command(command: Command) -> None:
        if isinstance(command, CreateServer):
            await QuartMegaMek._current_conductor().start_server(command.options)
        elif isinstance(command, DestroyServer):
            await QuartMegaMek._current_conductor().stop_server(command.id)


class ConfigVersionOption(BaseModel):
    mm_version: str
    mmconf: list[str]
    mechs: list[str]
    maps: list[str]


ConfigOptions = RootModel[dict[Version, ConfigVersionOption]]
