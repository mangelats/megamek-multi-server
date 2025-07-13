from aiofiles.tempfile import TemporaryDirectory
from asyncio import Event
from collections.abc import AsyncGenerator
from pathlib import Path
from pydantic import BaseModel, RootModel
from quart import current_app
from typing import Optional
import json
import os
import sys

import aiofiles
from quart import Quart

from .conductor import Conductor, ConductorConfig, Version
from .commands import Command, CreateServer, DestroyServer

_EXT_CODE = "QUART_MEGA_MECH"

class QuartMegaMek:
    _event: Event
    _conductor: Optional[Conductor]

    def __init__(self, app: Optional[Quart] = None) -> None:
        self._event = Event()
        self._conductor = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Quart) -> None:
        if _EXT_CODE in app.extensions:
            raise Exception("MegaMech extension has already been initialized")
        app.extensions[_EXT_CODE] = self
        app.before_serving(self._before_serving)
        app.after_serving(self._after_serving)
        
    async def _before_serving(self) -> None:
        current_app.add_background_task(self._run_conductor)

    async def _after_serving(self) -> None:
        """"""
        self._event.set()

    async def _run_conductor(self) -> None:
        if self._conductor is not None:
            raise Exception("A conductor is already working")

        config_file = sys.argv[1] or os.environ['MEGAMEK_MULTI_SERVER_CONFIG'] or './config.json'
        async with aiofiles.open(config_file, mode='r') as f:
            s: str = await f.read()
            config = json.loads(s)
            async with TemporaryDirectory() as temp_dir:
                server_configs = ConductorConfig(config["available_configs"])
                self._conductor = Conductor(Path(temp_dir), server_configs)
                await self._event.wait()
                await self._conductor.stop_all_servers()
                self._conductor = None

    @staticmethod
    def config_options() -> 'ConfigOptions':
        result: dict[Version, ConfigVersionOption] = {}
        for k, v in QuartMegaMek.current()._conductor.config.items():
            result[k] = ConfigVersionOption(
                mm_version=v.mm_version,
                mmconf=list(v.mmconf.keys()),
                mechs=list(v.mechs.keys()),
                maps=list(v.maps.keys()),
            )
        return ConfigOptions(result)

    @staticmethod
    def current() -> 'QuartMegaMek':
        return current_app.extensions[_EXT_CODE]
        
    @staticmethod
    def events() -> AsyncGenerator[Event, None]:
        return QuartMegaMek.current()._conductor.events()
    
    @staticmethod
    async def apply_command(command: Command) -> None:
        if isinstance(command, CreateServer):
            await QuartMegaMek.current()._conductor.start_server(command.options)
        elif isinstance(command, DestroyServer):
            await QuartMegaMek.current()._conductor.stop_server(command.id)


class ConfigVersionOption(BaseModel):
    mm_version: str
    mmconf: list[str]
    mechs: list[str]
    maps: list[str]

ConfigOptions = RootModel[dict[Version, ConfigVersionOption]]
