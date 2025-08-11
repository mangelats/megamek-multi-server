from collections.abc import Iterable
from datetime import timedelta

import psutil

from megamek_multi_server.utils.retry import retry


def next_port(ports: Iterable[int], used: set[int]) -> int:
    conns = psutil.net_connections(kind="inet")
    used = set(used)
    for c in conns:
        if c.laddr:
            used.add(c.laddr.port)
    try:
        return next(p for p in ports if p not in used)
    except StopIteration:
        raise Exception("No available ports")


def is_port_open(port: int) -> bool:
    return any(_is_port_open(c, port) for c in psutil.net_connections(kind="inet"))


def _is_port_open(c, port: int) -> bool:
    return c.laddr and c.laddr.port == port and c.status == psutil.CONN_LISTEN


async def wait_until_port_open(port: int, *, timeout: timedelta | None = None):
    await retry(
        lambda: _port_check(port),
        backoff_ratio=1.5,
        initial_wait=timedelta(seconds=1),
        timeout=timeout,
    )


async def _port_check(port: int) -> None | tuple:
    if is_port_open(port):
        return ()
    else:
        return None
