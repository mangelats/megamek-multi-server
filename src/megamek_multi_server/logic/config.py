from typing import Annotated, Optional

from pydantic import AliasChoices, BaseModel, Field

from .server_description import ServerDescription


class Config(BaseModel):
    passwords: str
    servers: dict[str, ServerDescription]
    max_servers: Optional[int] = Field(default=None, gt=0, alias="maxServers")
