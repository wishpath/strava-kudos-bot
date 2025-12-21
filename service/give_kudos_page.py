import asyncio
import logging
from typing import Any

from playwright.async_api import Page

from a_settings.props import Props
from c_storage.colors import Color
from service.console_print import ConsolePrint
from util.util import Util


class GiveKudosPage:
    def __init__(self, playwright_page: Page) -> None:
        self.playwright_page = playwright_page
        self.feed_entry_printer = ConsolePrint()

    def __getattr__(self, name: str) -> Any:
        """Called when accessing an attribute/method not defined on GiveKudosPage itself.
        Delegates the call to the underlying Playwright Page instance."""
        return getattr(self.playwright_page, name)

    # async def accept_cookies(self) -> None:
    #     try:
    #         cookie_banner_buttons = await self.playwright_page.wait_for_selector(
    #             "//div[@id='CybotCookiebotDialogBodyButtonsWrapper']", strict=True, timeout=3000)
    #         cookie_banner_accept_button = await cookie_banner_buttons.query_selector(
    #             "//button[@id='CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll']")
    #
    #         if cookie_banner_accept_button:
    #             await cookie_banner_accept_button.click()
    #         else:
    #             raise Exception("Cookie banner found but accept button not found.")
    #     except Exception as e:
    #         logger.info(f"No cookie banner found. {e}")

    async def accept_cookies(self) -> None:
        """find cookie banner"""
        try:
            cookie_banner_buttons = await self.playwright_page.wait_for_selector(
                "//div[@id='CybotCookiebotDialogBodyButtonsWrapper']", strict=True, timeout=3000)
        except Exception:
            return
        ConsolePrint.print_cookie_banner(cookie_banner_buttons)

        """find accept button"""
        cookie_accept_button = await cookie_banner_buttons.query_selector(
            "//button[@id='CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll']")
        await ConsolePrint.print_accepting_cookies(cookie_accept_button)
        if not cookie_accept_button:
            raise Exception("NO COOKIE ACCEPT BUTTON FOUND")

        """accept cookies"""
        await cookie_accept_button.click()

    async def do_login(self) -> None:
        """ensure we're on login page"""
        if not ("login" in self.playwright_page.url):
            await self.playwright_page.goto("https://www.strava.com/login", wait_until="load")
            await asyncio.sleep(1)

        """auto log-in"""
        login_buttons = await self.playwright_page.query_selector_all('//button[@data-testid="google_auth_btn"]')
        for btn in login_buttons:
            if await btn.is_visible():
                print(Color.GREEN + "Clicking log-in button" + Color.RESET)
                await btn.click(timeout=10000)
                break
        await asyncio.sleep(2)

        """manual log-in"""
        while "dashboard" not in self.playwright_page.url:
            print(Color.YELLOW + "Waiting for manual login" + Color.RESET)
            await asyncio.sleep(Props.user_manual_login_wait_cycle_seconds)
        print(Color.GREEN + "On dashboard page." + Color.RESET)

    async def loop_kudos_routines_with_cooldown_gaps(self) -> None:
        try:
            while True:
                """lazy loading entries"""
                for i in range(Props.count_of_scroll_to_bottom_of_page_to_load_entries):
                    ConsolePrint.print_loading_entries(i)
                    await self.scroll_to_bottom_of_page_to_load_entries()

                """deal feed entries"""
                await self.traverse_feed_entries()

                """cooldown gap"""
                await ConsolePrint.print_cooldown()
                await Util.sleep_minutes(Props.cooldown_minutes)
                await self.playwright_page.reload(wait_until="load")

        except asyncio.CancelledError:
            print("kudos routine cancelled")
            raise

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
        print(f"Feed entries loaded {feed_entries_count}")
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
