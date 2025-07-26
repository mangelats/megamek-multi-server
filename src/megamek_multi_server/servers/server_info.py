from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from .server import MegaMekServer, ServerState

class ServerInfo(BaseModel):
    id: UUID
    config_name: str
    mm_version: str
    port: int
    creator: Optional[str]
    creation_timestamp: datetime
    state: ServerState

    @staticmethod
    def from_server(server: MegaMekServer) -> "ServerInfo":
        return ServerInfo(
            id=server.id,
            config_name=server.config_name,
            mm_version=server.mm_version,
            port=server.port,
            creator=server.creator,
            creation_timestamp=server.creation_timestamp,
            state=server.state,
        )
