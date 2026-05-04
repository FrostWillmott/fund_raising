import os

from fund_raising.base import *

if os.getenv("DJANGO_ENV") == "production":
    import contextlib

    with contextlib.suppress(ImportError):
        from fund_raising.production import *  # noqa: F403
else:
    from fund_raising.development import *  # noqa: F403
