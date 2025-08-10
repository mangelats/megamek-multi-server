from collections.abc import Iterable

import psutil


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


def is_open(port: int) -> bool:
    return any(_is_conn_open(c, port) for c in psutil.net_connections(kind="inet"))


def _is_conn_open(c, port: int) -> bool:
    return c.laddr and c.laddr.port == port and c.status == psutil.CONN_LISTEN
