from typing import Any

from django.contrib.auth.models import User
from django.db import transaction

from api.cache import invalidate_cache
from collects.models import Collect
from collects.tasks import send_donation_email


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
            transaction.on_commit(
                lambda: send_donation_email.delay(
                    amount=str(collect.goal_amount),
                    title=collect.title,
                    email=created_by.email,
                )
            )
        transaction.on_commit(lambda: invalidate_cache("collects"))
    return collect
