import asyncio
import logging

from browser_manager import manager

logger = logging.getLogger(__name__)
# Remove existing handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s: %(message)s"
)

async def main() -> None:
    await manager.start_browser()

    try:
        page = await manager.new_page()
        await page.goto("https://www.strava.com/dashboard", wait_until="load")
        await page.accept_cookies()

        await page.do_login()

        await page.loop_kudos_routines_with_cooldown_gaps()
    finally:
        await manager.close_browser()


if __name__ == "__main__":
    asyncio.run(main())
