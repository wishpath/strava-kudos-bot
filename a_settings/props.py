class Props:

    """will scroll down at most this many times to load entries"""
    cap_count_of_scroll_to_bottom_of_page_to_load_entries = 10

    """cooldown between giving kudos"""
    cooldown_minutes = 5

    """name fragments, case ignored: """
    athletes_to_skip=[name.strip() for name in "wishpath".split(",") if name.strip()]

    """how often it will check if user has already logged-in manually"""
    user_manual_login_wait_cycle_seconds = 4
