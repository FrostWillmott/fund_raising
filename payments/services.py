from typing import Any

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import F
from rest_framework import exceptions

from collects.models import Collect
from fund_raising.cache import invalidate_cache
from fund_raising.utils import safe_enqueue_task
from payments.models import Payment
from payments.tasks import send_payment_email


def create_payment(*, payer: User, **validated_data: Any) -> Payment:
    """Single owner of the payment creation lifecycle.

    Owns the transaction, the forced COMPLETED status, the collected_amount
    increment, and the post-commit side effects (email, cache invalidation).
    Any other write path (admin, shell, bulk seeding) must maintain the
    counter itself.
    """
    with transaction.atomic():
        try:
            # Savepoint: an IntegrityError from a concurrent duplicate
            # transaction_id must not poison the outer transaction.
            with transaction.atomic():
                payment = Payment.objects.create(
                    payer=payer,
                    status=Payment.Status.COMPLETED,
                    **validated_data,
                )
        except IntegrityError as exc:
            raise exceptions.ValidationError(
                {"transaction_id": "transaction_id must be unique"}
            ) from exc

        collect_id = payment.collect_id
        if collect_id is not None:
            Collect.objects.filter(pk=collect_id).update(
                collected_amount=F("collected_amount") + payment.amount
            )

        payer_email = payment.payer.email if payment.payer else ""
        collect_title = payment.collect.title if payment.collect else ""
        if payer_email and collect_title:
            amount_str = str(payment.amount)
            transaction.on_commit(
                lambda: safe_enqueue_task(
                    send_payment_email.delay,
                    f"payment-email:{payer_email}",
                    amount=amount_str,
                    title=collect_title,
                    email=payer_email,
                )
            )
        # Payment list/retrieve are per-user and no longer cached; only the
        # collect pages (collected_amount, embedded feed) need invalidation.
        transaction.on_commit(lambda: invalidate_cache("collects"))
    return payment
