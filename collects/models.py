from decimal import Decimal

from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from collects.validators import validate_file_size


class Collect(models.Model):
    class Occasion(models.TextChoices):
        BIRTHDAY = "birthday", "Birthday"
        WEDDING = "wedding", "Wedding"
        NEW_YEAR = "new_year", "New Year"
        OTHER = "other", "Other"

    title = models.CharField(max_length=255, verbose_name="Title")
    occasion = models.CharField(
        max_length=20,
        choices=Occasion.choices,
        default=Occasion.OTHER,
        verbose_name="Occasion",
    )
    description = models.TextField(blank=True, verbose_name="Description")
    goal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave blank for an open-ended fundraise.",
        verbose_name="Goal amount",
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    collected_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Collected amount",
    )

    start_date = models.DateTimeField(
        default=timezone.now, verbose_name="Start date"
    )
    end_date = models.DateTimeField(
        null=True, blank=True, verbose_name="End date"
    )

    cover = models.ImageField(
        upload_to="collect_covers/%Y/%m/",
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_file_size,
        ],
        null=True,
        blank=True,
        verbose_name="Cover",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="collects",
        verbose_name="Author",
        null=True,
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Collect"
        verbose_name_plural = "Collects"
