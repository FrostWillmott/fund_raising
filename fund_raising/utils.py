import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def safe_enqueue_task(
    task_delay: Callable[..., Any],
    log_label: str,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Call ``task.delay(*args, **kwargs)``, logging instead of raising.

    A broker outage must not turn an already-committed write into a 500.
    """
    try:
        task_delay(*args, **kwargs)
    except Exception:
        logger.exception("Failed to enqueue %s task", log_label)
