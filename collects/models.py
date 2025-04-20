from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils import timezone


class Collect(models.Model):
    """Групповой денежный сбор."""

    class Occasion(models.TextChoices):
        BIRTHDAY = "birthday", "День рождения"
        WEDDING = "wedding", "Свадьба"
        NEW_YEAR = "new_year", "Новый год"
        OTHER = "other", "Другое"

    # ─────────── базовые реквизиты ───────────
    title = models.CharField(max_length=255, verbose_name="Название")
    occasion = models.CharField(
        max_length=20,
        choices=Occasion.choices,
        default=Occasion.OTHER,
        verbose_name="Повод",
    )
    description = models.TextField(blank=True, verbose_name="Описание")

    # ─────────── деньги ───────────
    goal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Оставьте пустым для нескончаемого сбора",
        verbose_name="Цель сбора",
    )
    collected_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Собрано",
    )

    # ─────────── даты ───────────
    start_date = models.DateTimeField(
        default=timezone.now, verbose_name="Дата начала"
    )
    end_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата окончания"
    )

    # ─────────── сервисные поля ───────────
    cover = models.ImageField(
        upload_to="collect_covers/",
        null=True,
        blank=True,
        verbose_name="Обложка",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="collects",
        verbose_name="Автор",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ─────────── вычислимые значения ───────────
    @property
    def donors_count(self) -> int:
        """Уникальное число пользователей, сделавших пожертвования."""
        return (
            self.payments.values("payer")
            .distinct()
            .count()
        )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Сбор"
        verbose_name_plural = "Сборы"
