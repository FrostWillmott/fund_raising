from django.db import models
from django.db.models import F
from django.conf import settings
from collects.models import Collect


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        COMPLETED = "completed", "Успешен"
        FAILED = "failed", "Неуспешен"

    collect = models.ForeignKey(
        Collect,
        on_delete=models.SET_NULL,
        related_name="payments",
        verbose_name="Сбор",
        null=True,
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="payments",
        verbose_name="Донатор",
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    payment_date = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """При первом успешном сохранении увеличиваем собранную сумму."""
        creating = self._state.adding
        super().save(*args, **kwargs)

        if creating and self.status == self.Status.COMPLETED:
            Collect.objects.filter(pk=self.collect_id).update(
                collected_amount=F("collected_amount") + self.amount
            )

    def __str__(self):
        return f"{self.collect.title} — {self.amount}"

    class Meta:
        ordering = ("-payment_date",)
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        indexes = [
            models.Index(fields=("collect", "status")),
        ]
