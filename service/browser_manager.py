import logging
from pathlib import Path

from playwright.async_api import async_playwright
from service.strava_page import StravaPage

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

STORAGE_DIR = Path(__file__).parent / 'playwright-state'


class BrowserManager:
    _instance = None

    def __new__(cls):
        """Create or return the singleton instance of BrowserManager,
        ensures there is a single browser instance in the app"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

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

        if STORAGE_DIR.exists():
            logger.info("Found saved authentication state")
        else:
            logger.info("No saved authentication state found - will save after first login")

        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(STORAGE_DIR),
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
