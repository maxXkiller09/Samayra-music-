"""Small, dependency-free parser for autoplay command actions."""

VALID_AUTOPLAY_ACTIONS = frozenset({"on", "off", "status", "next"})


def parse_autoplay_action(arguments):
    """Return a supported action, preserving the legacy no-argument toggle."""
    if not arguments:
        return "toggle"
    action = str(arguments[0]).strip().lower()
    if action in VALID_AUTOPLAY_ACTIONS:
        return action
    return "invalid"
