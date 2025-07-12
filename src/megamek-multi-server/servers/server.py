import aioshutil
import asyncio

from aiofiles.os import makedirs
from asyncio.subprocess import Process
from enum import Enum
from pathlib import Path
from typing import Callable, Optional
from uuid import UUID, uuid4

from .server_config import Mapping, ProcessArgs, ServerConfig


StateChanged = Callable[[UUID, 'ServerState'], None]

class MegaMekServer:
    _uuid: UUID
    _mm_version: str
    _port: int
    _state: 'ServerState'
    _path: Path
    _proc: Optional[Process]
    _config: ServerConfig
    _state_changed: Optional[StateChanged]

    @property
    def id(self) -> UUID:
        return self._uuid
    
    @property
    def mm_version(self) -> str:
        return self._mm_version
    
    @property
    def port(self) -> int:
        return self._port
    
    @property
    def state(self) -> 'ServerState':
        if self._proc is not None and self._proc.returncode is not None:
            return ServerState.zombie
        return self._state
    
    def __init__(
        self,
        mm_version: str,
        base: Path,
        config: ServerConfig,
        port: int,
        *,
        state_changed: Optional[StateChanged] = None,
    ) -> None:
        uuid = uuid4()
        path = base / str(uuid)

        self._uuid=uuid
        self._mm_version=mm_version
        self._port=port
        self._state=ServerState.fresh
        self._path=path
        self._proc=None
        self._config=config
        self._state_changed=state_changed

    async def start(self) -> None:
        """Starts the server with some config."""
        if self._state != ServerState.fresh:
            raise RuntimeError('Trying to start server where the state is not fresh')
        
        print(f"Starting server {self.id} on {self._port} at {self._path}")
        self._set_state(ServerState.setting_up)
        await self._set_up(self._config.mmconf, self._config.mechs, self._config.maps)
        self._set_state(ServerState.spawning)
        await self._spawn(self._config.process_args)
        self._set_state(ServerState.running)
    
    async def stop(self) -> None:
        """Starts the server with some config."""
        if self._state != ServerState.running:
            raise RuntimeError('Trying to stop server that\'s not running')
        
        self._set_state(ServerState.stopping)
        await self._stop()
        self._set_state(ServerState.cleaning_up)
        await self._clean_up()
        self._set_state(ServerState.dead)

    def _set_state(self, state: 'ServerState') -> None:
        self._state = state
        if self._state_changed is not None:
            self._state_changed(self._uuid, state)

    async def _set_up(self, mmconf: Mapping, mechs: Mapping, maps: Mapping) -> None:
        await makedirs(self._path / 'logs', mode=511, exist_ok=True)
        await mmconf.apply(self._path)
        await mechs.apply(self._path)
        await maps.apply(self._path)
        
    async def _spawn(self, process_args: ProcessArgs) -> None:
        self._proc = await asyncio.create_subprocess_exec(
            *process_args,
            "-dedicated",
            "-port",
            str(self._port),
            cwd=self._path,
        )
        # TODO: await for port or proper logs
        await asyncio.sleep(1)

    async def _stop(self) -> None:
        try:
            print("Attempting to terminate it gracefully (within 10 seconds)")
            async with asyncio.timeout(10):
                self._proc.terminate()
                await self._proc.wait()
        except TimeoutError:
            print("Forcefully kill it")
            self._proc.kill()
            await self._proc.wait()
        self._proc = None

    async def _clean_up(self) -> None:
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
