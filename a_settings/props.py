class Props:
    cap_count_of_scroll_to_bottom_of_page_to_load_entries = 10
    cooldown_minutes = 5
    athletes_to_skip=[name.strip() for name in "wishpath".split(",") if name.strip()]
    user_manual_login_wait_cycle_seconds = 4
