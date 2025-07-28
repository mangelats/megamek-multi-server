
from aiofiles.os import makedirs, symlink
from pathlib import Path
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field, RootModel


class ServerDescription(BaseModel):
    version: str
    exe: list[str]
    setup: 'ServerSetup'
    game: Optional[str]

class ServerSetup(RootModel):
    root: list['_Action']
    async def set_up_in(self, path: Path) -> None:
        for action in self.root:
            await action.apply_to(path)

class MkDir(BaseModel):
    type: Literal['mkdir'] = Field(default='mkdir')
    path: str

    async def apply_to(self, path: Path) -> None:
        try:
            await makedirs(path / self.path, mode=511)
        except FileExistsError:
            pass


class Link(BaseModel):
    type: Literal['link'] = Field(default='link')
    source: str
    target: str
    
    async def apply_to(self, path: Path) -> None:
        source = Path(self.source)
        target = Path(self.target)

        if not source.is_absolute():
            raise Exception("Sources need to be absolute")
        
        if target.is_absolute():
            raise Exception("Target needs to be relative")
        
        await symlink(source, path / target, target_is_directory=True)

        
_Action = Annotated[
    MkDir | Link,
    Field(discriminator="type"),
]