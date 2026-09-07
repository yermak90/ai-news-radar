from app.extractors.normalize import content_hash, normalize_title, normalize_url


class TestNormalizeUrl:
    def test_strips_tracking_params(self):
        # Host is lowercased; path case is preserved (some servers route case-sensitively).
        url = "https://Example.com/Post?utm_source=twitter&id=1"
        assert normalize_url(url) == "https://example.com/Post?id=1"

    def test_strips_www_and_fragment_and_trailing_slash(self):
        assert normalize_url("https://www.example.com/post/#section") == "https://example.com/post"

    def test_same_url_different_query_order_matches(self):
        a = normalize_url("https://example.com/post?b=2&a=1")
        b = normalize_url("https://example.com/post?a=1&b=2")
        assert a == b

    def test_different_paths_do_not_match(self):
        a = normalize_url("https://example.com/post-a")
        b = normalize_url("https://example.com/post-b")
        assert a != b


class TestNormalizeTitle:
    def test_lowercases_and_strips_punctuation(self):
        assert normalize_title("New Model: GPT-5 Released!") == "new model gpt 5 released"

    def test_collapses_whitespace(self):
        assert normalize_title("  Too   many   spaces  ") == "too many spaces"

    def test_equal_after_normalization(self):
        a = normalize_title("OpenAI releases GPT-5!")
        b = normalize_title("openai releases gpt 5")
        assert a == b


class TestContentHash:
    def test_same_title_and_body_produce_same_hash(self):
        assert content_hash("Title", "Body text") == content_hash("Title", "Body text")

    def test_different_body_produces_different_hash(self):
        assert content_hash("Title", "Body one") != content_hash("Title", "Body two")

    def test_hash_is_hex_sha256(self):
        h = content_hash("Title", "Body")
        assert len(h) == 64
        int(h, 16)  # raises ValueError if not valid hex
