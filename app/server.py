import aioshutil
import asyncio

from aiofiles.os import makedirs
from asyncio.subprocess import Process
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from .server_config import Mapping, ProcessArgs, ServerConfig


class MegaMekServer:
    _uuid: UUID
    _port: int
    _state: 'ServerState'
    _path: Path
    _proc: Optional[Process]

    @property
    def uuid(self) -> UUID:
        return self._uuid
    
    @property
    def state(self) -> 'ServerState':
        if self._proc is not None and self._proc.returncode is not None:
            return ServerState.zombie
        return self._state

    @staticmethod
    async def start(base: Path, config: ServerConfig, port: int) -> 'MegaMekServer':
        uuid = uuid4()
        path = base / str(uuid)
        print("Starting server at", path)

        server = MegaMekServer()
        server._uuid=uuid
        server._port=port
        server._state=ServerState.fresh
        server._path=path
        server._proc=None

        await server._start(config)
        return server

    async def _start(self, config: ServerConfig):
        """Starts the server with some config."""
        if self._state != ServerState.fresh:
            raise RuntimeError('Trying to start server where the state is not fresh')
        
        await self._set_state(ServerState.setting_up)
        await self._set_up(config.mmconf, config.mechs, config.maps)
        await self._set_state(ServerState.spawning)
        await self._spawn(config.process_args)
        await self._set_state(ServerState.running)
    
    async def stop(self):
        """Starts the server with some config."""
        if self._state != ServerState.running:
            raise RuntimeError('Trying to stop server that\'s not running')
        
        await self._set_state(ServerState.stopping)
        await self._stop()
        await self._set_state(ServerState.cleaning_up)
        await self._clean_up()
        await self._set_state(ServerState.dead)

    
    async def _set_state(self, state: 'ServerState'):
        self._state = state

    async def _set_up(self, mmconf: Mapping, mechs: Mapping, maps: Mapping):
        await makedirs(self._path / 'logs', mode=511, exist_ok=True)
        await mmconf.apply(self._path)
        await mechs.apply(self._path)
        await maps.apply(self._path)
        
    async def _spawn(self, process_args: ProcessArgs):
        self._proc = await asyncio.create_subprocess_exec(
            *process_args,
            "-dedicated",
            "-port",
            str(self._port),
            cwd=self._path,
        )
        # TODO: await for port or proper logs
        await asyncio.sleep(1)

    async def _stop(self):
        try:
            # Attempt to terminate it gracefully (10 seconds timeout)
            async with asyncio.timeout(10):
                await self._proc.terminate()
        except TimeoutError:
            # Forcefully kill it
            await self._proc.kill()
        self._proc = None

    async def _clean_up(self):
        await aioshutil.rmtree(self._path)
        

class ServerState(str, Enum):
    """Possible server states"""
    fresh = 'fresh'
    setting_up = 'setting_up'
    spawning = 'spawning'
    running = 'running'
    stopping = 'stopping'
    cleaning_up = 'cleaning_up'
    dead = 'dead'
    zombie = 'zombie'
