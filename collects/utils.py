from io import BytesIO
from pathlib import Path
from typing import Any

from django.core.files.base import ContentFile
from PIL import Image


def process_cover_image(instance: Any) -> None:
    """Resize and convert collection cover image to JPEG."""
    if not instance.cover:
        return

    img: Image.Image = Image.open(instance.cover)

    if img.width > 1200 or img.height > 800:
        img.thumbnail((1200, 800), Image.Resampling.LANCZOS)

    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)

    new_name = Path(instance.cover.name).stem + ".jpg"
    instance.cover.save(new_name, ContentFile(buffer.getvalue()), save=False)
