from typing import Any, List, Final
import asyncio

from playwright.async_api import async_playwright
from playwright.async_api import Page, Locator

from pathlib import Path

import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

STORAGE_DIR = Path(__file__).parent / 'playwright-state'


class StravaPage:
    def __init__(self, playwright_page: Page) -> None:
        """Strava page constructor: fields don't have to be predefined in the class"""
        self.playwright_page = playwright_page
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying Playwright Page instance.
        
        This allows the CustomPage to act as a proxy for the original Page object,
        providing transparent access to all Page methods and properties.
        
        Args:
            name: The name of the attribute to access.
            
        Returns:
            The attribute value from the underlying Page instance.
        """
        return getattr(self.playwright_page, name)
    
    async def is_on_dashboard_page__url_contains_dashboard(self) -> bool:
        return "dashboard" in self.playwright_page.url
    
    async def is_on_login_page(self) -> bool:
        return "login" in self.playwright_page.url
    
    async def refresh_page(self) -> None:
        await self.playwright_page.reload(wait_until="load")

    async def accept_cookies(self) -> None:
        """Automatically accept cookies if the cookie consent banner is present.

        This method waits few seconds for the cookie banner to appear, then clicks
        the "Accept All" button if found. If no banner is present - log entry is created.
        """
        try:
            cookie_banner_btns = await self.playwright_page.wait_for_selector("//div[@id='CybotCookiebotDialogBodyButtonsWrapper']", strict=True, timeout=3000)
            cookie_banner_accept_btn = await cookie_banner_btns.query_selector("//button[@id='CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll']")
            
            if cookie_banner_accept_btn:
                await cookie_banner_accept_btn.click()
            else:
                raise Exception("Cookie banner found but accept button not found.")
        except Exception as e:
            logger.info(f"No cookie banner found. {e}")
    
    async def do_login(self) -> None:
        """ Checks if on login page and performs login by clicking loging with Google
        and giving time for human to perform login manually.
        """
        if not await self.is_on_login_page():
            await self.playwright_page.goto("https://www.strava.com/login", wait_until="load")
            await asyncio.sleep(1)

        login_buttons = await self.playwright_page.query_selector_all('//button[@data-testid="google_auth_btn"]')
        logger.debug(f"Found {len(login_buttons)} buttons:")
        
        for btn in login_buttons:
            logger.debug(f"Button: {btn.text_content}")
            if await btn.is_visible():
                await btn.click(timeout=10000)
                logger.info(f"Clicked {btn}")
                break
            
        await asyncio.sleep(2)

        if not await self.is_on_dashboard_page__url_contains_dashboard():
            logger.info("Do a manual login.")
            await asyncio.sleep(50)
        else:
            logger.info("On dashboard page.")

    async def loop_kudos_routines_with_cooldown(self) -> None:
        twenty_minutes_in_seconds_between_kudos_routines: Final = 20 * 60

        try:
            while True: 
                for i in range(3):
                    logger.info(f"Scrolling: iteration: {i}")
                    await self.scroll_to_bottom_of_page()
                await self.click_all_visible_kudos_buttons()
                await asyncio.sleep(twenty_minutes_in_seconds_between_kudos_routines)
                self.refresh_page()

        except asyncio.CancelledError:
            logger.info("kudos routine cancelled")
            raise
    
    async def scroll_to_bottom_of_page(self) -> None:
        # Jump directly to the bottom of the page
        # This triggers lazy loading for new entries that appear when reaching the bottom
        await self.playwright_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)
        # Scroll slightly upward
        # Some sites only trigger loading fully after a tiny upward movement
        await self.playwright_page.evaluate("window.scrollBy(0, -200)")
        # Wait longer to ensure all new entries are loaded and rendered
        await asyncio.sleep(12)
        
    async def is_element_in_viewport(self, element: Locator) -> bool:
        """Checks if element is in browsers viewport.

        Args:
            element: The locator of element.
        
        Returns:
            True if the element is in browsers viewport, False otherwise.
        """
        box = await element.bounding_box()
        if not box:
            return False

        viewport = await self.playwright_page.evaluate(
            "() => ({ width: window.innerWidth, height: window.innerHeight })"
        )

        top = box["y"]
        bottom = box["y"] + box["height"]

        return not (bottom < 0 or top > viewport["height"])
    
    async def click_all_visible_kudos_buttons(self) -> None:
        athletes_to_skip=[name.strip() for name in "wishpath".split(",") if name.strip()]
        """
        Click all visible kudos buttons that have not yet been clicked.
        This method: locates all kudos buttons currently in the viewport, filters out those already clicked, 
        licks each remaining kudos button.
        
        Notes:
            Scrolling must be performed **after** calling this method 
            in order to reveal additional buttons outside the current view.
        """
        feed_entries = self.playwright_page.locator("div[data-testid='web-feed-entry']")
        feed_entries_count = await feed_entries.count()

        logger.debug(f"Feed entries count {feed_entries_count}")

        for i in range(feed_entries_count):
            feed_entry = feed_entries.nth(i)

            kudos_buttons = feed_entry.locator("//button[@data-testid='kudos_button']")
            kudos_buttons_count = await kudos_buttons.count()

            logger.info(30 * "-")
            logger.info(f"Kudos buttons count {kudos_buttons_count}")

            for j in range(kudos_buttons_count):
                kudos_button = kudos_buttons.nth(j)

                if kudos_buttons_count == 1:
                    owner_name = feed_entry.locator("//a[@data-testid='owners-name']")
                    owner_name = await owner_name.inner_text()
                elif kudos_buttons_count >= 2:
                    entry_li = kudos_button.locator("xpath=ancestor::li[.//*[@data-testid='entry-header']]")
                    owner_name = entry_li.locator("//a[@data-testid='owners-name']").first
                    owner_name = await owner_name.inner_text()
                    
                logger.info(f"Owner: {owner_name}")

                unfilled_kudos_button = kudos_button.locator("svg[data-testid='unfilled_kudos']")
                is_unfilled = await unfilled_kudos_button.count() > 0

                if not is_unfilled:
                    logger.info("-> Already clicked.")
                    continue

                if athletes_to_skip and any(athlete.lower() in owner_name.lower() for athlete in athletes_to_skip):
                    logger.info("-> Skipping.")
                    continue

                await kudos_button.click()
                logger.info("-> Clicked.")
            
            await asyncio.sleep(1)

    async def do_scroll(self, num_of_scrolls: int = 1, scroll_px: int = 800) -> None:
        """
        Scroll the page a specified number of times.

        Args:
            num_of_scrolls (int, optional):
                The number of scroll actions to perform. Defaults to 1.
            scroll_px (int, optional):
                Number of pixels to scroll down on each scroll action. Defaults to 800.

        Notes:
            Each scroll action should move the viewport enough to reveal
            new kudos buttons for `give_kudos()` to process.
        """
        for _ in range(num_of_scrolls):
            await self.playwright_page.mouse.wheel(0, scroll_px)
            await asyncio.sleep(5000)


class BrowserManager:
    """A singleton manager for Playwright browser instances and contexts.
    
    This class implements the Singleton pattern to ensure only one browser instance
    is active throughout the application lifecycle. It manages the browser context
    with persistent state storage for authentication and session management.
    """
    _instance = None

    def __new__(cls):
        """Create or return the singleton instance of BrowserManager.
        
        Returns:
            The singleton BrowserManager instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the BrowserManager with None values for playwright and context."""
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
            viewport={"width": 1440, "height": 900},
            locale="en-US",
            timezone_id="Europe/Vilnius",
            service_workers="allow",
            permissions=["geolocation"],
            geolocation={"latitude": 54.6872, "longitude": 25.2797},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--mute-audio"
            ],
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    
    async def new_page(self) -> StravaPage:
        page = await self.context.new_page()
        return StravaPage(page)
    
    async def close_browser(self) -> None:
        """Close the browser context and stop Playwright.
        
        This method performs a graceful shutdown by:
        1. Closing the browser context (if it exists)
        2. Stopping the Playwright instance (if it exists)
        """
        if self.context:
            await self.context.close()
        
        if self.playwright:
            await self.playwright.stop()


manager = BrowserManager()
