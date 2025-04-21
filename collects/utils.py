from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image


def process_cover_image(instance):
    """Optimize and resize collection cover images."""
    if not instance.cover:
        return

    # Open image
    img = Image.open(instance.cover)

    # Process if needed (resize, optimize)
    if img.width > 1200 or img.height > 800:
        img.thumbnail((1200, 800), Image.LANCZOS)

    # Save optimized version
    # Convert image to RGB if it has an alpha channel
    if img.mode in ('RGBA', 'LA'):
        img = img.convert('RGB')
    img.save(buffer, format='JPEG', quality=85, optimize=True)

    # Replace original file
    instance.cover.save(
        instance.cover.name,
        ContentFile(buffer.getvalue()),
        save=False
    )
