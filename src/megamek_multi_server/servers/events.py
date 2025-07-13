from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field

from .server import ServerState
from .server_info import ServerInfo


class EventType(str, Enum):
    servers_set='servers_set'
    server_added='server_added'
    server_state_changed='server_state_changed'
    server_removed='server_removed'


class BaseEvent(BaseModel):
    """Shared data for all events."""
    event_timestamp: datetime = Field(default_factory=datetime.now)


class ServersSet(BaseEvent):
    """Set the list of current servers. This is useful as the starting event."""
    event_type: Literal[EventType.servers_set] = Field(default=EventType.servers_set)
    servers: list[ServerInfo]

class ServerAdded(BaseEvent):
    """A server has been added."""
    event_type: Literal[EventType.server_added] = Field(default=EventType.server_added)
    info: ServerInfo

class ServerStateChanged(BaseEvent):
    """A server has changed its state."""
    event_type: Literal[EventType.server_state_changed] = Field(default=EventType.server_state_changed)
    id: UUID
    new_state: ServerState

class ServerRemoved(BaseEvent):
    """A server was removed and no longer exists."""
    event_type: Literal[EventType.server_removed] = Field(default=EventType.server_removed)
    id: UUID


Event = Annotated[
    ServersSet | ServerAdded | ServerStateChanged | ServerRemoved,
    Field(discriminator="event_type"),
]
