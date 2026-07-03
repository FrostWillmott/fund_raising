import smtplib

from celery import shared_task
from django.core.mail import send_mail


@shared_task(
    autoretry_for=(OSError, smtplib.SMTPException),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_donation_email(amount: str, title: str, email: str) -> None:
    "An email to the author regarding the creation of a collection (or another purpose)."
    send_mail(
        subject="Collect created",
        message=f'You have created a fundraise "{title}" with a goal of {amount}. Good luck!',
        recipient_list=[email],
        from_email=None,
    )


@shared_task
def deactivate_expired_collects() -> int:
    """Mark all collects past their end_date as inactive."""
    from django.utils import timezone

    from collects.models import Collect

    updated = Collect.objects.filter(
        is_active=True,
        end_date__lt=timezone.now(),
    ).update(is_active=False)
    return updated
