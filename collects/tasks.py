from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_donation_email(amount: str, title: str, email: str) -> None:
    """Письмо автору о создании сбора (или другое назначение)."""
    send_mail(
        subject="Сбор создан",
        message=f"Вы создали сбор «{title}» с целью {amount} ₽. Удачи!",
        recipient_list=[email],
        from_email=None,
        fail_silently=True,
    )
