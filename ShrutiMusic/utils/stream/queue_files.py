"""Helpers for replacing placeholder queue entries with downloaded files."""


def replace_tracked_file(queue, tracked_files, old_file, new_file):
    """Replace one queue placeholder and its cleanup reference after download."""
    if not new_file or not queue or queue[0].get("file") != old_file:
        return False

    try:
        tracked_files.remove(old_file)
    except ValueError:
        pass
    tracked_files.append(new_file)
    queue[0]["file"] = new_file
    return True
