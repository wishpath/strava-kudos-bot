from c_storage.colors import Color


class FeedEntryPrintService:

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
