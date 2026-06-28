from django.conf import settings
from django.db import models
from django.db.models import F

from collects.models import Collect


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    collect = models.ForeignKey(
        Collect,
        on_delete=models.SET_NULL,
        related_name="payments",
        verbose_name="Collect",
        null=True,
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="payments",
        verbose_name="Payer",
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
        creating = self._state.adding
        super().save(*args, **kwargs)

        if creating and self.status == self.Status.COMPLETED:
            Collect.objects.filter(pk=self.collect_id).update(
                collected_amount=F("collected_amount") + self.amount
            )

    def __str__(self):
        title = self.collect.title if self.collect else "—"
        return f"{title} — {self.amount}"

    class Meta:
        ordering = ("-payment_date",)
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=("collect", "status")),
        ]
