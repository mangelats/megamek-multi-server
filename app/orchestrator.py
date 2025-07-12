from pathlib import Path
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from .server import MegaMekServer, ServerState
from .server_config import ProcessArgs, Mapping, ServerConfig

Version = str

class Orchestrator:
    _options: dict[Version, 'Options']
    base_path: Path
    _servers: dict[UUID, MegaMekServer]
    _aquired_ports: set[int]

    def __init__(self, base_path: Path, config: 'OrchestratorConfig'):
        self.base_path = base_path
        self._options = config.options
        self._servers = {}
        self._aquired_ports = set()

    async def start_server(self, selection: 'Selection') -> UUID:
        options = self._options[selection.version]
        config = ServerConfig(
            process_args=options.process,
            mmconf=options.mmconf[selection.mmconf],
            mechs=options.mechs[selection.mechs],
            maps=options.maps[selection.maps],
        )
        port = self._aquire_port()
        try:
            server = await MegaMekServer.start(options.mm_version, self.base_path, config, port)
            self._servers[server.id] = server
            return server.id
        except Exception as e:
            self._aquired_ports.remove(port)
            raise e
    
    async def stop_server(self, server_id: UUID):
        server = self._servers[server_id]
        port = server.port
        try:
            await server.stop()
        finally:
            del self._servers[server_id]
            self._aquired_ports.remove(port)
    
    def get_server_info(self, server_id: UUID) -> 'ServerInfo':
        server = self._servers[server_id]
        return ServerInfo(
            id=server.id,
            mm_version=server.mm_version,
            port=server.port,
            state=server.state,
        )

    def _aquire_port(self) -> int:
        for i in range(2346, 65535):
            if i not in self._aquired_ports:
                self._aquired_ports.add(i)
                return i
        raise Exception('All ports are full (WTF happened?)')


class OrchestratorConfig(BaseModel):
    options: dict[Version, 'Options']

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

class Selection(BaseModel):
    version: Version
    mmconf: str
    mechs: str
    maps: str

class ServerInfo(BaseModel):
    id: UUID
    mm_version: str
    port: int
    state: ServerState
