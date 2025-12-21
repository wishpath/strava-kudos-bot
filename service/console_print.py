from datetime import datetime, timedelta

from a_settings.props import Props
from c_storage.colors import Color


class ConsolePrint:

    async def print_clicking(self, feed_entry, owner_name: str) -> None:
        distance_locator = feed_entry.locator("li:has(span:has-text('Distance')) div.vNsSU").first
        distance = await distance_locator.text_content() if await distance_locator.count() else ""

        activity_locator = feed_entry.locator("svg[data-testid='activity-icon'] title").first
        activity_type = await activity_locator.evaluate(
            "el => el.textContent") if await activity_locator.count() else ""

        time_locator = feed_entry.locator("time[data-testid='date_at_time']").first
        start_time = await time_locator.inner_text() if await time_locator.count() else ""

        url_locator = feed_entry.locator("a[data-testid='activity_name']").first
        activity_url = await url_locator.get_attribute("href") if await url_locator.count() else ""
        activity_url = f"https://www.strava.com{activity_url}" if activity_url else ""

        title = await url_locator.text_content() if await url_locator.count() else ""

        print(f"{Color.GREEN}{owner_name}{Color.RESET}, "
              f"kudos button: {Color.CYAN}clicking now{Color.RESET}, "
              f"{Color.YELLOW}{activity_type}{Color.RESET}, "
              f"{start_time}, "
              f"{Color.GREY}{distance}{Color.RESET}, "
              f"{activity_url}, "
              f"{Color.CYAN}{title}{Color.RESET}")

    @staticmethod
    async def print_cooldown():
        print(f"\nCooldown: {Props.cooldown_minutes} minutes. Next routine starts at: "
              f"{(datetime.now() + timedelta(minutes=Props.cooldown_minutes)).strftime('%H:%M')}")
        print("*" * 60 + "\n\n")

    @staticmethod
    async def print_loading_entries(i):
        print(f"Scrolling down to load feed entries: iteration: {i + 1}"
                    f"/{Props.count_of_scroll_to_bottom_of_page_to_load_entries}")

    @staticmethod
    async def print_cookie_banner(cookie_banner_buttons):
        if cookie_banner_buttons:
            print(f"{Color.YELLOW}Cookie banner found{Color.RESET}")
        else:
            print(f"{Color.GREY}No cookie banner found{Color.RESET}")

    @staticmethod
    async def print_accepting_cookies(cookie_accept_button):
        if cookie_accept_button:
            print(f"{Color.CYAN}Clicking accept cookies button{Color.RESET}")
        else:
            print(f"{Color.GREY}No accept button found{Color.RESET}")