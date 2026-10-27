"""Small, secret-safe validation helpers for assistant session configuration."""


def duplicate_session_slots(session_values):
    """Return pairs of slot names that contain the same non-empty session string.

    The session value itself is never returned, so callers can report conflicts
    without risking accidental credential disclosure in logs.
    """
    first_slot_by_value = {}
    duplicates = []
    for slot_name, session_value in session_values:
        if not session_value:
            continue
        normalized = session_value.strip()
        if not normalized:
            continue
        first_slot = first_slot_by_value.get(normalized)
        if first_slot is not None:
            duplicates.append((first_slot, slot_name))
        else:
            first_slot_by_value[normalized] = slot_name
    return duplicates
