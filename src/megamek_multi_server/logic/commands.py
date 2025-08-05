from enum import Enum
from typing import Annotated, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CommandType(str, Enum):
    create_server = "create_server"
    destroy_server = "destroy_server"


class CreateServer(BaseModel):
    """Asks the server to create a new MegaMek server."""

    cmd_type: Literal[CommandType.create_server] = Field(default=CommandType.create_server)
    server: str
    id: Optional[UUID]


class DestroyServer(BaseModel):
    """Asks the server to stop and destroy a new MegaMek server."""

    cmd_type: Literal[CommandType.destroy_server] = Field(default=CommandType.destroy_server)
    id: UUID


Command = Annotated[
    CreateServer | DestroyServer,
    Field(discriminator="cmd_type"),
]
