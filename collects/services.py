import logging
from typing import Any

from django.contrib.auth.models import User
from django.db import transaction

from collects.models import Collect
from collects.tasks import process_cover_image_task, send_donation_email
from fund_raising.cache import invalidate_cache

logger = logging.getLogger(__name__)


def _enqueue_collect_email(amount: str, title: str, email: str) -> None:
    # A broker outage must not turn an already-committed collect into a 500.
    try:
        send_donation_email.delay(amount=amount, title=title, email=email)
    except Exception:
        logger.exception("Failed to enqueue collect email to %s", email)


def _enqueue_cover_processing(collect_id: int) -> None:
    # A broker outage must not turn an already-committed collect into a 500.
    try:
        process_cover_image_task.delay(collect_id)
    except Exception:
        logger.exception(
            "Failed to enqueue cover processing for collect %s", collect_id
        )


def create_collect(*, created_by: User, **validated_data: Any) -> Collect:
    """Single owner of the collect creation lifecycle.

    Owns the transaction and the post-commit side effects (cover processing,
    author email, cache invalidation).
    """
    with transaction.atomic():
        collect = Collect.objects.create(
            created_by=created_by, **validated_data
        )
        if collect.cover:
            collect_id = collect.id
            transaction.on_commit(
                lambda: _enqueue_cover_processing(collect_id)
            )
        if created_by and created_by.email:
            author_email = created_by.email
            goal_amount = str(collect.goal_amount or "open-ended")
            title = collect.title
            transaction.on_commit(
                lambda: _enqueue_collect_email(
                    goal_amount, title, author_email
                )
            )
        transaction.on_commit(lambda: invalidate_cache("collects"))
    return collect
