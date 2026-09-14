import re

# fallback chain: edgartools' parsed object attribute, then a regex slice
# of the raw filing text, then give up and flag for manual review

ITEM_1A_REGEX = re.compile(
    r"item\s+1a\.?\s*risk factors(.*?)item\s+1b\.?",
    re.IGNORECASE | re.DOTALL,
)


def extract_via_object(tenk_obj):
    if tenk_obj is None:
        return None
    try:
        text = tenk_obj.risk_factors
    except AttributeError:
        return None
    if text and text.strip():
        return text
    return None


def extract_via_regex(full_text):
    if not full_text:
        return None
    match = ITEM_1A_REGEX.search(full_text)
    if not match:
        return None
    text = match.group(1).strip()
    return text or None


def extract_item_1a(tenk_obj=None, full_text=None):
    """
    Try tenk_obj.risk_factors first, then regex "Item 1A" -> "Item 1B" on
    full_text. Returns None if both fail so the caller can flag the filing
    for manual review instead of failing silently.
    """
    text = extract_via_object(tenk_obj)
    if text:
        return text

    text = extract_via_regex(full_text)
    if text:
        return text

    return None
