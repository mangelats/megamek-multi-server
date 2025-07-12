from pathlib import Path
import aiofiles
import asyncio
import json
import os
import sys
from aiofiles.tempfile import TemporaryDirectory
from pprint import pprint

from ..app.server import MegaMekServer, ServerConfig
from ..app.orchestrator import Orchestrator, Selection, OrchestratorConfig

async def main():
    config_file = sys.argv[1] or os.environ['MEGAMEK_MULTI_SERVER_CONFIG'] or './config.json'
    async with aiofiles.open(config_file, mode='r') as f:
        s: str = await f.read()
        config = json.loads(s)
        async with TemporaryDirectory() as temp_dir:
            server_configs = OrchestratorConfig(options=config["available_configs"])
            orchestrator = Orchestrator(Path(temp_dir), server_configs)

            servers = await asyncio.gather(
                orchestrator.start_server(Selection(
                    version="0.49",
                    mmconf="default",
                    mechs="default",
                    maps="default",
                )),
                orchestrator.start_server(Selection(
                    version="0.50",
                    mmconf="default",
                    mechs="default",
                    maps="default",
                )),
            )
            try:
                while True:
                    for s in servers:
                        info = orchestrator.get_server_info(s)
                        print(info)
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                await asyncio.gather(*(orchestrator.stop_server(s) for s in servers))

def _simple_config(config) -> ServerConfig:
    return ServerConfig(
        process_args=config['process'],
        mmconf=config['mmconf'][0],
        mechs=config['mechs'][0],
        maps=config['maps'][0],
    )

if __name__ == "__main__":
    asyncio.run(main())
