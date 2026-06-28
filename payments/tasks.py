from decimal import Decimal

from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_payment_email(amount: Decimal, title: str, email: str) -> None:
    send_mail(
        subject="Thank you for your donation!",
        message=f'You donated {amount} to the fundraise "{title}".',
        recipient_list=[email],
        from_email=None,
        fail_silently=True,
    )
