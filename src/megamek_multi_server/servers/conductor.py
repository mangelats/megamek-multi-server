import asyncio
from asyncio import Queue
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Iterable
from uuid import UUID

from pydantic import BaseModel, RootModel

from .events import Event, ServerAdded, ServerRemoved, ServersSet, ServerStateChanged
from .server import MegaMekServer, ServerState
from .server_config import Mapping, ProcessArgs, ServerConfig
from .server_info import ServerInfo

Version = str

class Conductor:
    _config: 'ConductorConfig'
    base_path: Path
    _servers: dict[UUID, MegaMekServer]
    _aquired_ports: set[int]
    _queues: set[Queue[Event]]

    def __init__(self, base_path: Path, config: 'ConductorConfig') -> None:
        self.base_path = base_path
        self._config = config
        self._servers = {}
        self._aquired_ports = set()
        self._queues = set()
    
    @property
    def config(self) -> 'ConductorConfig':
        return self._config

    async def start_server(self, selection: 'OptionSelection') -> UUID:
        options = self._config[selection.version]
        config = ServerConfig(
            process_args=options.process,
            mmconf=options.mmconf[selection.mmconf],
            mechs=options.mechs[selection.mechs],
            maps=options.maps[selection.maps],
        )
        port = self._aquire_port()
        try:
            server = MegaMekServer(
                options.mm_version,
                self.base_path,
                config,
                port,
                state_changed=self._state_changed
            )
            self._broadcast_event(ServerAdded(info=ServerInfo.from_server(server)))
            self._servers[server.id] = server
            await server.start()
            return server.id
        except Exception as e:
            self._aquired_ports.remove(port)
            raise e
        
    async def stop_all_servers(self) -> None:
        servers = self._servers
        self._servers = {}
        self._aquired_ports = set()
        await asyncio.gather(*(server.stop() for server in servers.values()))

    async def stop_server(self, server_id: UUID) -> None:
        server = self._servers[server_id]
        port = server.port
        try:
            await server.stop()
        finally:
            del self._servers[server_id]
            self._aquired_ports.remove(port)
            self._broadcast_event(ServerRemoved(id=server_id))
    
    def all_servers_info(self) -> list['ServerInfo']:
        return [ServerInfo.from_server(server) for server in self._servers.values()]

    def server_info(self, server_id: UUID) -> 'ServerInfo':
        server = self._servers[server_id]
        return ServerInfo.from_server(server)

    def _aquire_port(self) -> int:
        for i in range(2346, 65535):
            if i not in self._aquired_ports:
                self._aquired_ports.add(i)
                return i
        raise Exception('All ports are full (WTF happened?)')
    
    async def events(self) -> AsyncGenerator[Event, None]:
        queue: Queue[Event] = Queue()
        self._queues.add(queue)
        yield ServersSet(servers=self.all_servers_info())
        try:
            while True:
                yield await queue.get()
                queue.task_done()
        finally:
            self._queues.remove(queue)

    def _state_changed(self, id: UUID, new_state: ServerState) -> None:
        self._broadcast_event(ServerStateChanged(id=id, new_state=new_state))

    def _broadcast_event(self, event: Event) -> None:
        for q in self._queues:
            # TODO: limit number of pending events
            q.put_nowait(event)


class ConductorConfig(RootModel):
    root: dict[Version, 'Options']
    
    def items(self) -> Iterable[tuple[Version, 'Options']]:
        return self.root.items()
    
    def keys(self) -> Iterable[Version]:
        return self.root.keys()
    
    def values(self) -> Iterable['Options']:
        return self.root.values()

    def __getitem__(self, item: Version) -> 'Options':
        return self.root[item]

class Options(BaseModel):
    """
    Definition of available options
    (combine different options to make a valid ServerConfig)
    """
    process: ProcessArgs
    mm_version: str
    mmconf: dict[str, Mapping]
    mechs: dict[str, Mapping]
    maps: dict[str, Mapping]

class OptionSelection(BaseModel):
    """Information that defined what option is used."""
    version: Version
    mmconf: str
    mechs: str
    maps: str
