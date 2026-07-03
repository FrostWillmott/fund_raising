import smtplib

from celery import shared_task
from django.core.mail import send_mail


@shared_task(
    autoretry_for=(OSError, smtplib.SMTPException),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_payment_email(amount: str, title: str, email: str) -> None:
    send_mail(
        subject="Thank you for your donation!",
        message=f'You donated {amount} to the fundraise "{title}".',
        recipient_list=[email],
        from_email=None,
    )
