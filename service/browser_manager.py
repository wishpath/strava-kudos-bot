from pathlib import Path

from playwright.async_api import async_playwright
from service.strava_page import StravaPage

class BrowserManager:
    _singleton = None

    """create sigleton object instance"""
    def __new__(this_class):
        this_class._singleton = super().__new__(this_class) if this_class._singleton is None else this_class._singleton
        return this_class._singleton
    """initial fields setter: 'self' refers to the the object returned by __new__"""
    def __init__(self) -> None:
        self.playwright = None
        self.context = None

    async def start_browser(self) -> None:
        """Start the Playwright browser with a persistent context.
        
        This method initializes Playwright (if not already started) and launches a
        browser with persistent storage.
        
        The persistent context ensures that login sessions and cookies are maintained
        across browser restarts.
        """
        if not self.playwright:
            self.playwright = await async_playwright().start()

        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(Path(__file__).resolve().parents[1] / "c_storage" / "playwright-state"),
            headless=False,
            channel="chrome",
            # viewport={"width": 1440, "height": 900},
            locale="en-US",
            timezone_id="Europe/Vilnius",
            service_workers="allow",
            permissions=["geolocation"],
            geolocation={"latitude": 54.91782439745546, "longitude": 23.833729337385112},

            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--mute-audio",
                "--start-maximized"
            ],
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    async def new_page(self) -> StravaPage:
        page = await self.context.new_page()
        return StravaPage(page)

    async def close_browser(self) -> None:
        if self.context:
            await self.context.close()

        if self.playwright:
            await self.playwright.stop()


manager = BrowserManager()
