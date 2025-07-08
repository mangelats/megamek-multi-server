from dataclasses import dataclass

@dataclass
class ServerConfig:
    """Definition on how to create a server"""
    process: list[str]
    mmconf_source: str
    

def new_server():
    pass
