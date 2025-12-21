import asyncio


class Util:
    @staticmethod
    async def sleep_minutes(minutes: int) -> None:
        await asyncio.sleep(minutes * 60)