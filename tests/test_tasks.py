from datetime import timedelta
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from collects.tasks import (
    deactivate_expired_collects,
    process_cover_image_task,
)


def _make_cover(
    width: int, height: int, fmt: str = "PNG"
) -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new("RGB", (width, height), color=(100, 150, 200)).save(
        buf, format=fmt
    )
    buf.seek(0)
    ext = "jpg" if fmt == "JPEG" else fmt.lower()
    return SimpleUploadedFile(
        f"test.{ext}", buf.read(), content_type=f"image/{fmt.lower()}"
    )


@pytest.mark.django_db
class TestDeactivateExpiredCollects:
    def test_deactivates_only_expired_active_collects(self, collect_factory):
        # Active, not expired — should stay active.
        active = collect_factory(
            is_active=True,
            end_date=timezone.now() + timedelta(days=1),
        )
        # Active but expired — should be deactivated.
        expired = collect_factory(
            is_active=True,
            end_date=timezone.now() - timedelta(days=1),
        )
        # Already inactive — should stay inactive.
        already_inactive = collect_factory(
            is_active=False,
            end_date=timezone.now() - timedelta(days=1),
        )
        # Active with no end_date — should stay active.
        open_ended = collect_factory(
            is_active=True,
            end_date=None,
        )

        updated_count = deactivate_expired_collects()

        assert updated_count == 1
        active.refresh_from_db()
        assert active.is_active is True
        expired.refresh_from_db()
        assert expired.is_active is False
        already_inactive.refresh_from_db()
        assert already_inactive.is_active is False
        open_ended.refresh_from_db()
        assert open_ended.is_active is True

    def test_returns_zero_when_nothing_to_deactivate(self, collect_factory):
        collect_factory(
            is_active=True, end_date=timezone.now() + timedelta(days=1)
        )
        collect_factory(is_active=False)

        assert deactivate_expired_collects() == 0


@pytest.mark.django_db
class TestProcessCoverImageTask:
    def test_resizes_oversized_image(self, collect_factory):
        collect = collect_factory(cover=_make_cover(2000, 1500, fmt="JPEG"))

        process_cover_image_task(collect.id)

        collect.refresh_from_db()
        img = Image.open(collect.cover)
        assert img.width <= 1200
        assert img.height <= 800

    def test_converts_png_to_jpeg(self, collect_factory):
        collect = collect_factory(cover=_make_cover(100, 100, fmt="PNG"))

        process_cover_image_task(collect.id)

        collect.refresh_from_db()
        assert collect.cover.name.endswith(".jpg")
        # The original PNG file should be replaced by JPEG content.
        img = Image.open(collect.cover)
        assert img.format == "JPEG"

    def test_noop_on_missing_collect(self):
        # Must not raise — the task may fire after a collect was deleted.
        process_cover_image_task(99999)

    def test_noop_on_collect_without_cover(self, collect_factory):
        collect = collect_factory(cover=None)

        # Must not raise.
        process_cover_image_task(collect.id)
