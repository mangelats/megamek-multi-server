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
            config = config["available_configs"]["0.49"]
            server_config = ServerConfig(
                process_args=config['process'],
                mmconf=config['mmconf'][0],
                mechs=config['mechs'][0],
                maps=config['maps'][0],
            )
            server = await MegaMekServer.start(temp_dir, server_config, 2347)
            while True:
                await asyncio.sleep(10)
                print('Server state', server.state)
            


if __name__ == "__main__":
    asyncio.run(main())
