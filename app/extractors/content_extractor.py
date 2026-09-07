from dataclasses import dataclass

from bs4 import BeautifulSoup

_NOISE_TAGS = ("nav", "footer", "header", "aside", "script", "style", "form", "noscript", "iframe")
_NOISE_CLASS_HINTS = (
    "cookie",
    "sidebar",
    "menu",
    "navbar",
    "advert",
    "banner",
    "subscribe",
    "newsletter",
    "related",
    "share",
    "social",
    "footer",
    "breadcrumb",
)

MAX_TEXT_LENGTH = 20_000  # bound extracted text size (PRD section 50, "ограничить размер")


@dataclass(frozen=True)
class ExtractedContent:
    title: str | None
    text: str
    author: str | None


def _looks_noisy(tag) -> bool:
    class_and_id = " ".join(tag.get("class", [])) + " " + (tag.get("id") or "")
    class_and_id = class_and_id.lower()
    return any(hint in class_and_id for hint in _NOISE_CLASS_HINTS)


def extract_content(html: str | None, fallback_text: str = "") -> ExtractedContent:
    """Best-effort extraction of the readable body of an article (PRD section 12).

    Strips nav/footer/ads/cookie banners/sidebars. Falls back to whatever
    text is available (e.g. RSS summary) if HTML parsing yields nothing.
    """
    if not html:
        return ExtractedContent(title=None, text=fallback_text.strip()[:MAX_TEXT_LENGTH], author=None)

    soup = BeautifulSoup(html, "lxml")

    for tag_name in _NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in soup.find_all(True):
        if _looks_noisy(tag):
            tag.decompose()

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    author_tag = soup.find(attrs={"name": "author"}) or soup.find(rel="author")
    author = None
    if author_tag is not None:
        author = author_tag.get("content") or author_tag.get_text(strip=True) or None

    main = soup.find("article") or soup.find("main") or soup.body or soup
    text = main.get_text(separator="\n", strip=True) if main else ""
    text = text or fallback_text.strip()

    if not text:
        text = fallback_text.strip()

    return ExtractedContent(title=title, text=text[:MAX_TEXT_LENGTH], author=author)
