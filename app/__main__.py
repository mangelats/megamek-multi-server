from pathlib import Path
import aiofiles
import asyncio
import json
import os
import sys
from aiofiles.tempfile import TemporaryDirectory
from pprint import pprint

from .server import MegaMekServer, ServerConfig

async def main():
    config_file = sys.argv[1] or os.environ['MEGAMEK_MULTI_SERVER_CONFIG'] or './config.json'
    async with aiofiles.open(config_file, mode='r') as f:
        s: str = await f.read()
        config = json.loads(s)
        async with TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            available_configs = config["available_configs"]

            servers = await asyncio.gather(
                MegaMekServer.start(
                    temp_dir,
                    _simple_config(available_configs["0.49"]),
                    2349,
                ),
                MegaMekServer.start(
                    temp_dir,
                    _simple_config(available_configs["0.50"]),
                    2350,
                ),
            )
            try:
                while True:
                    print('Server 0 state', servers[0].state)
                    print('Server 1 state', servers[1].state)
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                await asyncio.gather(*(s.stop() for s in servers))

def _simple_config(config) -> ServerConfig:
    return ServerConfig(
        process_args=config['process'],
        mmconf=config['mmconf'][0],
        mechs=config['mechs'][0],
        maps=config['maps'][0],
    )

if __name__ == "__main__":
    asyncio.run(main())
