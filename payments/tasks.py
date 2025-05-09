from decimal import Decimal

from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_payment_email(amount: Decimal, title: str, email: str) -> None:
    send_mail(
        subject="Спасибо за пожертвование!",
        message=f"Вы пожертвовали {amount} на сбор «{title}».",
        recipient_list=[email],
        from_email=None,
        fail_silently=True,
    )
