import logging
from typing import Any

from django.contrib.auth.models import User
from django.db import transaction

from collects.models import Collect
from collects.tasks import send_donation_email
from fund_raising.cache import invalidate_cache

logger = logging.getLogger(__name__)


def _enqueue_collect_email(amount: str, title: str, email: str) -> None:
    # A broker outage must not turn an already-committed collect into a 500.
    try:
        send_donation_email.delay(amount=amount, title=title, email=email)
    except Exception:
        logger.exception("Failed to enqueue collect email to %s", email)


def create_collect(*, created_by: User, **validated_data: Any) -> Collect:
    """Single owner of the collect creation lifecycle.

    Owns the transaction and the post-commit side effects (author email,
    cache invalidation).
    """
    with transaction.atomic():
        collect = Collect.objects.create(
            created_by=created_by, **validated_data
        )
        if created_by and created_by.email:
            author_email = created_by.email
            transaction.on_commit(
                lambda: _enqueue_collect_email(
                    str(collect.goal_amount), collect.title, author_email
                )
            )
        transaction.on_commit(lambda: invalidate_cache("collects"))
    return collect
