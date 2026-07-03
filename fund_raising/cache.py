from django.core.cache import cache


def invalidate_cache(*patterns: str) -> None:
    """Delete cached pages whose keys contain any of the given patterns.

    django-redis extends the standard cache API with ``delete_pattern``;
    backends without it (LocMemCache in tests) fall back to a full clear —
    over-invalidation is harmless there.
    """
    delete_pattern = getattr(cache, "delete_pattern", None)
    if delete_pattern is None:
        cache.clear()
        return
    for pattern in patterns:
        delete_pattern(f"*{pattern}*")
