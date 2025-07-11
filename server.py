import os
from pathlib import Path
from subprocess import Popen
from pydantic import BaseModel, ConfigDict
from uuid import uuid4

ProcessArgs = list[str]


class Orchestrator:
    """Helps creating and destroying servers"""
    base: Path

    def new_server(self, config: 'ServerConfig') -> 'Server':
        path = self.base / uuid4()

        config.mmconf.apply(path)
        config.mechs.apply(path)
        config.maps.apply(path)
        
        
        return Server(path=path, process=process)


class Server(BaseModel):
    path: Path
    process: Popen[str]

    def close(self):
        self.process.terminate()
        self.process.wait(timeout=)

    def force_close(self):
        self.process.kill()


class Mapping(BaseModel):
    """From somewhere to somewhere"""
    model_config = ConfigDict(strict=True)
    sources: list[Path]
    dest: Path

    def apply(self, base: Path):
        dest = base / self.dest
        if len(self.sources) == 1 and self.sources[0].is_dir():
            os.symlink(self.sources[0], dest, target_is_directory=True)
        
        dest.mkdir(mode=511, parents = True)
        for src in self.sources:
            link_dest = dest / os.path.basename(src)
            os.symlink(src, link_dest, target_is_directory=src.is_dir())


class ServerConfig(BaseModel):
    """Definition on how to create a server"""
    model_config = ConfigDict(strict=True)
    process: ProcessArgs
    mmconf: Mapping
    mechs: Mapping
    maps: Mapping


class ServerAvailableConfigs(BaseModel):
    """
    Definition of available options
    (combine different options to make a valid ServerConfig)
    """
    model_config = ConfigDict(strict=True)
    process: ProcessArgs
    mmconf: list[Mapping]
    mechs: list[Mapping]
    maps: list[Mapping]
    
