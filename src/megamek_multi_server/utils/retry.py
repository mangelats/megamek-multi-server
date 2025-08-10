import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import TypeVar

T = TypeVar("T")


async def retry(
    f: Callable[[], Awaitable[T | None]],
    *,
    backoff_ratio: float = 1,
    backoff_increment: timedelta = timedelta(),
    initial_wait: timedelta = timedelta(),
    timeout: timedelta | None = None,
) -> T:
    if timeout is not None:
        t = timeout.total_seconds()
    else:
        t = None

    return await asyncio.wait_for(
        _retry(
            f,
            backoff_ratio=backoff_ratio,
            backoff_increment=backoff_increment,
            initial_wait=initial_wait,
        ),
        timeout=t,
    )


async def _retry(
    f: Callable[[], Awaitable[T | None]],
    *,
    backoff_ratio: float,
    backoff_increment: timedelta,
    initial_wait: timedelta,
) -> T:
    wait = initial_wait * backoff_ratio

    while True:
        await asyncio.sleep(wait.total_seconds())
        wait = wait * backoff_ratio + backoff_increment

        result = await f()
        if result is not None:
            return result
