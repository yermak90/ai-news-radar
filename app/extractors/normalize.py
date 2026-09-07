import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_TRACKING_PARAM_PREFIXES = ("utm_", "ref", "fbclid", "gclid", "mc_cid", "mc_eid", "igshid")
_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]")


def normalize_url(url: str) -> str:
    """Canonicalize a URL for exact-match deduplication (PRD section 13.1, Level 1).

    - lowercases scheme/host
    - strips fragment
    - strips known tracking query params
    - strips trailing slash
    """
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    netloc = netloc.removeprefix("www.")

    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not any(k.lower().startswith(prefix) for prefix in _TRACKING_PARAM_PREFIXES)
    ]
    query = urlencode(sorted(query_pairs))

    path = parsed.path.rstrip("/") or "/"

    return urlunparse((scheme, netloc, path, "", query, ""))


def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation/whitespace for fuzzy title comparison (Level 2)."""
    lowered = title.strip().lower()
    lowered = _NON_ALNUM_RE.sub(" ", lowered)
    return _WHITESPACE_RE.sub(" ", lowered).strip()


def content_hash(title: str, body: str) -> str:
    """Stable hash of normalized title + body, used for Level 3 exact-content dedup."""
    normalized = normalize_title(title) + "|" + _WHITESPACE_RE.sub(" ", body.strip().lower())[:2000]
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
