from os.path import basename, dirname
from pathlib import Path

from aiofiles.os import makedirs, symlink
from aiofiles.ospath import isdir
from pydantic import BaseModel

ProcessArgs = list[str]


class Mapping(BaseModel):
    """From somewhere to somewhere"""

    sources: list[str]
    target: str

    async def apply(self, base: Path) -> None:
        dest = base / self.target
        if len(self.sources) == 1 and await isdir(self.sources[0]):
            parent = dirname(dest)
            await ensure_path(parent)
            await symlink(self.sources[0], dest, target_is_directory=True)
        else:
            await ensure_path(dest)
            for src in self.sources:
                link_dest = dest / basename(src)
                is_dir = await isdir(src)
                await symlink(src, link_dest, target_is_directory=is_dir)


async def ensure_path(path) -> None:
    try:
        await makedirs(path, mode=511)
    except FileExistsError:
        pass


class ServerConfig(BaseModel):
    """Definition on how to create a server"""

    process_args: ProcessArgs
    mmconf: Mapping
    mechs: Mapping
    maps: Mapping
