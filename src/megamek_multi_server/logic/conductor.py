import asyncio
from asyncio import Queue
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Optional
from uuid import UUID

from megamek_multi_server.utils.net import next_port

from .events import Event, ServerAdded, ServerRemoved, ServersSet, ServerStateChanged
from .server import MegaMekServer, ServerState
from .server_description import ServerDescription
from .server_info import ServerInfo


class Conductor:
    _descriptions: dict[str, ServerDescription]
    base_path: Path
    _servers: dict[UUID, MegaMekServer]
    _aquired_ports: set[int]
    _queues: set[Queue[Event]]

    def __init__(self, base_path: Path, descriptions: dict[str, ServerDescription]) -> None:
        self.base_path = base_path
        self._descriptions = descriptions
        self._servers = {}
        self._aquired_ports = set()
        self._queues = set()

    def server_descriptions(self) -> list[str]:
        return list(self._descriptions.keys())

    async def start_server(
        self, config_name: str, id: Optional[UUID], creator: Optional[str]
    ) -> UUID:
        description = self._descriptions[config_name]

        port = self._aquire_port()
        try:
            server = MegaMekServer(
                config_name=config_name,
                description=description,
                base=self.base_path,
                port=port,
                state_changed=self._state_changed,
                id=id,
                creator=creator,
            )
            self._broadcast_event(ServerAdded(info=ServerInfo.from_server(server)))
            self._servers[server.id] = server
            await server.start()
            return server.id
        except Exception as e:
            self._aquired_ports.remove(port)
            raise e

    async def shutdown(self) -> None:
        await self.stop_all_servers()
        queues = self._queues
        self._queues = set()
        for queue in queues:
            queue.shutdown()

    async def stop_all_servers(self) -> None:
        await asyncio.gather(*(self.stop_server(id) for id in self._servers.keys()))

    async def stop_server(self, server_id: UUID) -> None:
        server = self._servers[server_id]
        try:
            await server.stop()
        except Exception as e:
            # The process may have crashed or something. The dead state may not
            # be propegated, so we clean it up.
            self._remove_server(server_id)
            raise e

    def all_servers_info(self) -> list[ServerInfo]:
        return [ServerInfo.from_server(server) for server in self._servers.values()]

    def server_info(self, server_id: UUID) -> ServerInfo:
        server = self._servers[server_id]
        return ServerInfo.from_server(server)

    def _aquire_port(self) -> int:
        port = next_port(range(2346, 65535), self._aquired_ports)
        self._aquired_ports.add(port)
        return port

    async def events(self) -> AsyncGenerator[Event, None]:
        queue: Queue[Event] = Queue()
        self._queues.add(queue)
        yield ServersSet(servers=self.all_servers_info())  # TODO remove from here
        try:
            while True:
                yield await queue.get()
                queue.task_done()
        finally:
            self._queues.remove(queue)

    def _state_changed(self, server_id: UUID, new_state: ServerState) -> None:
        self._broadcast_event(ServerStateChanged(id=server_id, new_state=new_state))
        if new_state == ServerState.dead:
            self._remove_server(server_id)

    def _remove_server(self, server_id: UUID) -> None:
        server = self._servers.get(server_id)
        if server is None:
            # This can be called multiple times in some edge cases.
            return

        del self._servers[server_id]
        self._broadcast_event(ServerRemoved(id=server_id))
        self._aquired_ports.remove(server.port)

    def _broadcast_event(self, event: Event) -> None:
        for q in self._queues:
            # TODO: limit number of pending events
            q.put_nowait(event)
