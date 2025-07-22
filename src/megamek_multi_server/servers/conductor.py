import asyncio
from asyncio import Queue
from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import UUID

from pydantic import RootModel

from .events import Event, ServerAdded, ServerRemoved, ServersSet, ServerStateChanged
from .server import MegaMekServer, ServerState
from .server_description import ServerDescription
from .server_info import ServerInfo

AvailableServerDescriptions = RootModel[dict[str, ServerDescription]]

class Conductor:
    _descriptions: dict[str, ServerDescription]
    base_path: Path
    _servers: dict[UUID, MegaMekServer]
    _aquired_ports: set[int]
    _queues: set[Queue[Event]]

    def __init__(self, base_path: Path, descriptions: AvailableServerDescriptions) -> None:
        self.base_path = base_path
        self._descriptions = descriptions.root
        self._servers = {}
        self._aquired_ports = set()
        self._queues = set()

    def server_descriptions(self) -> list[str]:
        return list(self._descriptions.keys())

    async def start_server(self, config_name: str) -> UUID:
        description = self._descriptions[config_name]

        port = self._aquire_port()
        try:
            server = MegaMekServer(
                description, self.base_path, port, state_changed=self._state_changed
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

    def all_servers_info(self) -> list["ServerInfo"]:
        return [ServerInfo.from_server(server) for server in self._servers.values()]

    def server_info(self, server_id: UUID) -> "ServerInfo":
        server = self._servers[server_id]
        return ServerInfo.from_server(server)

    def _aquire_port(self) -> int:
        for i in range(2346, 65535):
            if i not in self._aquired_ports:
                self._aquired_ports.add(i)
                return i
        raise Exception("All ports are full (WTF happened?)")

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
