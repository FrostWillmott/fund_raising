from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_donation_email(amount: str, title: str, email: str) -> None:
    "An email to the author regarding the creation of a collection (or another purpose)."
    send_mail(
        subject="Сбор создан",
        message=f"Вы создали сбор «{title}» с целью {amount} ₽. Удачи!",
        recipient_list=[email],
        from_email=None,
        fail_silently=True,
    )
