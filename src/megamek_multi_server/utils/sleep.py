import asyncio
from datetime import datetime
from typing import Awaitable, TypeVar

T = TypeVar("T")


async def wait_until(when: datetime) -> None:
    delta = when - datetime.now(tz=when.tzinfo)
    await asyncio.sleep(delta.total_seconds())


async def run_at(when: datetime, coro: Awaitable[T]) -> T:
    await wait_until(when)
    return await coro


def schedule_at(when: datetime, coro: Awaitable[T]) -> asyncio.Task:
    return asyncio.create_task(run_at(when, coro))
