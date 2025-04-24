from io import BytesIO
from typing import Any

from django.core.files.base import ContentFile
from PIL import Image


def process_cover_image(instance: Any) -> None:
    """Optimize and resize collection cover images."""
    if not instance.cover:
        return

    img = Image.open(instance.cover)

    if img.width > 1200 or img.height > 800:
        img.thumbnail((1200, 800), Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True)

    instance.cover.save(
        instance.cover.name,
        ContentFile(buffer.getvalue()),
        save=False
    )
