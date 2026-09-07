from html import escape

TELEGRAM_MESSAGE_LIMIT = 4096
_SAFE_MARGIN = 200  # leave room so we never split mid-tag by accident


def escape_html(text: str) -> str:
    return escape(text, quote=False)


def chunk_messages(blocks: list[str], *, separator: str = "\n\n") -> list[str]:
    """Pack text blocks into as few Telegram messages as possible, respecting the 4096 char limit."""
    limit = TELEGRAM_MESSAGE_LIMIT - _SAFE_MARGIN
    messages: list[str] = []
    current = ""

    for block in blocks:
        block = block[:limit]  # a single block should never exceed the limit on its own
        candidate = f"{current}{separator}{block}" if current else block
        if len(candidate) > limit:
            if current:
                messages.append(current)
            current = block
        else:
            current = candidate

    if current:
        messages.append(current)

    return messages
