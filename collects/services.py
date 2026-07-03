from typing import Any

from django.contrib.auth.models import User
from django.db import transaction

from collects.models import Collect
from collects.tasks import process_cover_image_task, send_donation_email
from fund_raising.cache import invalidate_cache
from fund_raising.utils import safe_enqueue_task


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
                lambda: safe_enqueue_task(
                    process_cover_image_task.delay,
                    f"cover-processing:{collect_id}",
                    collect_id,
                )
            )
        if created_by and created_by.email:
            author_email = created_by.email
            goal_amount = str(collect.goal_amount or "open-ended")
            title = collect.title
            transaction.on_commit(
                lambda: safe_enqueue_task(
                    send_donation_email.delay,
                    f"collect-email:{author_email}",
                    amount=goal_amount,
                    title=title,
                    email=author_email,
                )
            )
        transaction.on_commit(lambda: invalidate_cache("collects"))
    return collect
