from datetime import datetime, timedelta
from typing import Any
import asyncio
from playwright.async_api import Page
import logging
from a_settings.props import Props
from c_storage.colors import Color
from service.feed_entry_print_service import FeedEntryPrintService

logger = logging.getLogger(__name__)


class GiveKudosPage:
    def __init__(self, playwright_page: Page) -> None:
        self.playwright_page = playwright_page
        self.feed_entry_printer = FeedEntryPrintService()

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

    async def accept_cookies(self) -> None:
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
        if not ("login" in self.playwright_page.url):
            await self.playwright_page.goto("https://www.strava.com/login", wait_until="load")
            await asyncio.sleep(1)

        login_buttons = await self.playwright_page.query_selector_all('//button[@data-testid="google_auth_btn"]')
        logger.debug(f"Found {len(login_buttons)} login buttons:")

        for btn in login_buttons:
            logger.debug(f"Button: {btn.text_content}")
            if await btn.is_visible():
                await btn.click(timeout=10000)
                logger.info(f"Clicked {btn}")
                break

        await asyncio.sleep(2)

        if not ("dashboard" in self.playwright_page.url):
            logger.info("Do a manual login.")
            await asyncio.sleep(50)
        else:
            logger.info("On dashboard page.")

    async def loop_kudos_routines_with_cooldown_gaps(self) -> None:
        try:
            while True:
                """kudos routine of lazy loading entries and clicking"""
                for i in range(Props.count_of_scroll_to_bottom_of_page_to_load_entries):
                    logger.info(f"Scrolling down to load feed entries: iteration: {i + 1}"
                                f"/{Props.count_of_scroll_to_bottom_of_page_to_load_entries}")
                    await self.scroll_to_bottom_of_page_to_load_entries()
                await self.traverse_feed_entries()

                """cooldown gap"""
                logger.info(f"\nCooldown: {Props.cooldown_minutes} minutes. Next routine starts at: "
                            f"{(datetime.now() + timedelta(minutes=Props.cooldown_minutes)).strftime('%H:%M')}")
                logger.info("*" * 60 + "\n\n")
                await self.sleep_minutes(Props.cooldown_minutes)
                await self.playwright_page.reload(wait_until="load")

        except asyncio.CancelledError:
            logger.info("kudos routine cancelled")
            raise

    async def sleep_minutes(self, minutes: int) -> None:
        await asyncio.sleep(minutes * 60)

    async def scroll_to_bottom_of_page_to_load_entries(self) -> None:
        # Jump directly to the bottom of the page
        # This triggers lazy loading for new entries that appear when reaching the bottom
        await self.playwright_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)
        # Scroll slightly upward
        # Some sites only trigger loading fully after a tiny upward movement
        await self.playwright_page.evaluate("window.scrollBy(0, -200)")
        # Wait longer to ensure all new entries are loaded and rendered
        await asyncio.sleep(12)

    async def traverse_feed_entries(self) -> None:
        """Getting all feed entries"""
        feed_entries = self.playwright_page.locator("div[data-testid='web-feed-entry']")
        feed_entries_count = await feed_entries.count()
        logger.debug(f"Visible feed entries count {feed_entries_count}")
        """Dealing all feed entries"""
        for i in range(feed_entries_count):
            await self.deal_single_feed_entry(feed_entries.nth(i))
            await asyncio.sleep(1)

    async def deal_single_feed_entry(self, feed_entry):
        single_entry_kudos_buttons = feed_entry.locator("//button[@data-testid='kudos_button']")
        single_entry_kudos_buttons_count = await single_entry_kudos_buttons.count()
        for j in range(single_entry_kudos_buttons_count):
            kudos_button = single_entry_kudos_buttons.nth(j)
            owner_name = await self.get_owners_name(feed_entry, kudos_button, single_entry_kudos_buttons_count)

            """Skipping blacklisted athlete"""
            if await self.is_athlete_in_the_skipping_list(owner_name):
                await feed_entry.scroll_into_view_if_needed()
                print(f"{Color.GREY}Skipping blacklisted athlete: {owner_name}{Color.RESET}")
                continue

            """Skipping already clicked button"""
            unclicked_kudos_buttons = kudos_button.locator("svg[data-testid='unfilled_kudos']")
            if not (await unclicked_kudos_buttons.count() > 0):
                await feed_entry.scroll_into_view_if_needed()
                print(f"{Color.GREY}{owner_name}: Kudos were already clicked before {Color.RESET}")
                continue

            """clicking kudos"""
            await self.feed_entry_printer.print_clicking(feed_entry, owner_name)
            await kudos_button.click()

    async def is_athlete_in_the_skipping_list(self, owner_name):
        athlete_is_in_skipping_list = (
                Props.athletes_to_skip and
                any(athlete.lower() in owner_name.lower() for athlete in Props.athletes_to_skip)
        )
        return athlete_is_in_skipping_list

    async def get_owners_name(self, feed_entry, kudos_button, kudos_buttons_count):
        if kudos_buttons_count == 1:
            owner_name = feed_entry.locator("//a[@data-testid='owners-name']")
            owner_name = await owner_name.inner_text()
        elif kudos_buttons_count >= 2:
            entry_li = kudos_button.locator("xpath=ancestor::li[.//*[@data-testid='entry-header']]")
            owner_name = entry_li.locator("//a[@data-testid='owners-name']").first
            owner_name = await owner_name.inner_text()
        return owner_name