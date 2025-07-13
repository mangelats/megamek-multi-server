from uuid import UUID

from pydantic import BaseModel

from .server import MegaMekServer, ServerState


class ServerInfo(BaseModel):
    id: UUID
    mm_version: str
    port: int
    state: ServerState

    @staticmethod
    def from_server(server: MegaMekServer) -> 'ServerInfo':
        return ServerInfo(
            id=server.id,
            mm_version=server.mm_version,
            port=server.port,
            state=server.state,
        )
