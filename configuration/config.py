class Config:
    count_of_scroll_to_bottom_of_page_to_load_entries = 1  #1 is minimum
    cooldown_minutes = 5
    athletes_to_skip=[name.strip() for name in "wishpath".split(",") if name.strip()]