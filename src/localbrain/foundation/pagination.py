from typing import List, Optional


def pagination_items(current_page: int, total_pages: int) -> List[Optional[int]]:
    """Return a compact, ordered page list with ``None`` as an ellipsis."""
    if total_pages <= 7:
        return list(range(1, total_pages + 1))

    window_start = max(2, current_page - 1)
    window_end = min(total_pages - 1, current_page + 1)
    if current_page <= 3:
        window_end = 4
    elif current_page >= total_pages - 2:
        window_start = total_pages - 3

    items: List[Optional[int]] = [1]
    if window_start > 2:
        items.append(None)
    items.extend(range(window_start, window_end + 1))
    if window_end < total_pages - 1:
        items.append(None)
    items.append(total_pages)
    return items


def compact_pagination_items(
    current_page: int, total_pages: int
) -> List[Optional[int]]:
    """Return at most five pagination tokens for the narrow viewport."""
    if total_pages <= 5:
        return list(range(1, total_pages + 1))
    if current_page <= 2:
        return [1, 2, 3, None, total_pages]
    if current_page >= total_pages - 1:
        return [1, None, total_pages - 2, total_pages - 1, total_pages]
    return [1, None, current_page, None, total_pages]
