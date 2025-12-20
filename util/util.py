import asyncio


class Util:
    async def sleep_minutes(self, minutes: int) -> None:
        await asyncio.sleep(minutes * 60)