def mask_api_key(key: str) -> str:
    if not key or len(key) < 8:
        return "****"
    prefix_len = 3 if key.startswith("sk-") else 2
    suffix_len = 4
    return key[:prefix_len] + "****" + key[-suffix_len:]
