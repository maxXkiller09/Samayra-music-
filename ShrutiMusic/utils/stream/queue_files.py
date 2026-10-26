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



def replace_tracked_queue_item(queue, tracked_files, item, old_file, new_file):
    """Replace a specific queued placeholder after a background prefetch finishes."""
    if not new_file or not queue or item.get("file") != old_file:
        return False
    if not any(queued is item for queued in queue):
        return False

    try:
        tracked_files.remove(old_file)
    except ValueError:
        pass
    tracked_files.append(new_file)
    item["file"] = new_file
    return True
