from pydantic import BaseModel

from .server_description import ServerDescription


class Config(BaseModel):
    passwords: str
    servers: dict[str, ServerDescription]
