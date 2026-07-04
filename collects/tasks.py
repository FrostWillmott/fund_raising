import smtplib

from celery import shared_task
from django.core.mail import send_mail


@shared_task(
    autoretry_for=(OSError, smtplib.SMTPException),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_collect_created_email(amount: str, title: str, email: str) -> None:
    send_mail(
        subject="Collect created",
        message=f'You have created a fundraise "{title}" with a goal of {amount}. Good luck!',
        recipient_list=[email],
        from_email=None,
    )


@shared_task(
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_cover_image_task(collect_id: int) -> None:
    """Resize and re-encode a collect cover image to JPEG (1200×800 max).

    Runs asynchronously so the HTTP request cycle never blocks on Pillow.
    Retries on filesystem errors (OSError) with exponential backoff.
    ``PIL.UnidentifiedImageError`` (a subclass of ``OSError``) is caught
    explicitly — retrying a corrupt file is pointless.
    """
    from PIL import UnidentifiedImageError

    from collects.models import Collect
    from collects.utils import process_cover_image
    from fund_raising.cache import invalidate_cache

    # Lock the row so a concurrent cover upload during processing doesn't get
    # overwritten by the processed version of the old image.
    try:
        collect = Collect.objects.select_for_update().get(pk=collect_id)
    except Collect.DoesNotExist:
        return

    if not collect.cover:
        return

    try:
        process_cover_image(collect)
    except UnidentifiedImageError:
        # Corrupt file — retrying won't help.
        return

    collect.save(update_fields=["cover", "updated_at"])
    # The cover URL changed (new filename/format); cached collect pages
    # still hold the old URL and must be invalidated again.
    invalidate_cache("collects")


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
