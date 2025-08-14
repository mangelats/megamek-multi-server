from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .server import ServerState
from .server_info import ServerInfo


class EventType(str, Enum):
    config_changed = "config_changed"
    servers_set = "servers_set"
    server_added = "server_added"
    server_state_changed = "server_state_changed"
    server_removed = "server_removed"
    error = "error"


class BaseEvent(BaseModel):
    """Shared data for all events."""

    event_timestamp: datetime = Field(default_factory=datetime.now)


class ConfigChange(BaseEvent):
    """Some configuration changed."""

    event_type: Literal[EventType.config_changed] = Field(default=EventType.config_changed)
    max_servers: Optional[int]


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

    event_type: Literal[EventType.server_state_changed] = Field(
        default=EventType.server_state_changed
    )
    id: UUID
    new_state: ServerState


class ServerRemoved(BaseEvent):
    """A server was removed and no longer exists."""

    event_type: Literal[EventType.server_removed] = Field(default=EventType.server_removed)
    id: UUID


class Error(BaseEvent):
    """Some error ocurred."""

    event_type: Literal[EventType.error] = Field(default=EventType.error)
    name: str
    message: str
    extra_data: dict[str, Any]


Event = Annotated[
    ConfigChange | ServersSet | ServerAdded | ServerStateChanged | ServerRemoved | Error,
    Field(discriminator="event_type"),
]
