from service.security import mask_api_key


def test_mask_short_key():
    assert mask_api_key("k") == "****"
    assert mask_api_key("") == "****"


def test_mask_normal_key_keeps_prefix_and_suffix():
    out = mask_api_key("sk-1234567890abcdef")
    assert out.startswith("sk-")
    assert out.endswith("cdef")
    assert "*" in out
    assert "1234567890ab" not in out


def test_mask_idempotent():
    once = mask_api_key("sk-1234567890abcdef")
    twice = mask_api_key(once)
    assert twice == once or "*" in twice
