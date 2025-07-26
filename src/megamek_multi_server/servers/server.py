import asyncio
from asyncio.subprocess import Process
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional
from uuid import UUID, uuid4

import aioshutil
from .server_description import ServerDescription, ServerSetup

StateChanged = Callable[[UUID, "ServerState"], None]


class MegaMekServer:
    _uuid: UUID
    _config_name: str
    _server_description: ServerDescription
    _path: Path
    _port: int
    _creator: Optional[str]
    _creation_timestamp: datetime

    _state_changed: Optional[StateChanged]

    _proc: Optional[Process]
    _state: "ServerState"

    @property
    def id(self) -> UUID:
        return self._uuid

    @property
    def config_name(self) -> str:
        return self._config_name

    @property
    def mm_version(self) -> str:
        return self._server_description.version

    @property
    def port(self) -> int:
        return self._port

    @property
    def creator(self) -> int:
        return self._creator
    
    @property
    def creation_timestamp(self) -> datetime:
        return self._creation_timestamp
    
    @property
    def state(self) -> "ServerState":
        if self._proc is not None and self._proc.returncode is not None:
            return ServerState.zombie
        return self._state

    def __init__(
        self,
        config_name: str,
        description: ServerDescription,
        base: Path,
        port: int,
        *,
        state_changed: Optional[StateChanged] = None,
        id: Optional[UUID] = None,
        creator: Optional[str] = None,
    ) -> None:
        self._uuid = id or uuid4()
        self._config_name = config_name
        self._server_description = description
        self._path = base / str(self._uuid)
        self._port = port
        self._creator = creator
        self._creation_timestamp = datetime.now()
        print(self._creation_timestamp)

        self._state_changed = state_changed

        self._proc = None
        self._state = ServerState.fresh

    async def start(self) -> None:
        """Starts the server with some config."""
        if self._state != ServerState.fresh:
            raise RuntimeError("Trying to start server where the state is not fresh")

        print(f"Starting server {self.id} on {self._port} at {self._path}")
        self._set_state(ServerState.setting_up)
        await self._set_up()
        self._set_state(ServerState.spawning)
        await self._spawn(self._server_description.exe)
        self._set_state(ServerState.running)

    async def stop(self) -> None:
        """Starts the server with some config."""
        if self._state != ServerState.running:
            raise RuntimeError("Trying to stop server that's not running")

        self._set_state(ServerState.stopping)
        await self._stop()
        self._set_state(ServerState.cleaning_up)
        await self._clean_up()
        self._set_state(ServerState.dead)

    def _set_state(self, state: "ServerState") -> None:
        self._state = state
        if self._state_changed is not None:
            self._state_changed(self._uuid, state)

    async def _set_up(self) -> None:
        await self._server_description.setup.set_up_in(self._path)

    async def _spawn(self, process_args: list[str]) -> None:
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
        if self._proc is None:
            raise Exception("Trying to close a process that does not exist (how did we get here?)")
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
        await aioshutil.rmtree(self._path, ignore_errors=True)


class ServerState(str, Enum):
    """Possible server states"""

    fresh = "fresh"
    setting_up = "setting_up"
    spawning = "spawning"
    running = "running"
    stopping = "stopping"
    cleaning_up = "cleaning_up"
    dead = "dead"
    zombie = "zombie"
