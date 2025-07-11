from pathlib import Path
from pydantic import BaseModel, ConfigDict

from .server import MegaMekServer
from .server_config import ProcessArgs, Mapping

Version = str

class Orchestrator:
    available_configs: dict[Version, 'ServerAvailableConfigs']
    base_path: Path
    _servers: dict[int, MegaMekServer]

    def __init__(self, base_path: Path, available_configs: dict[Version, 'ServerAvailableConfigs']):
        self.base_path = base_path
        self.available_configs = available_configs
        self._servers = {}


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