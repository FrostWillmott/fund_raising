from django.db.models.signals import pre_save
from django.dispatch import receiver

from collects.models import Collect
from collects.utils import process_cover_image


@receiver(pre_save, sender=Collect)
def handle_cover_image(sender, instance, **kwargs):
    new_cover_name = instance.cover.name if instance.cover else None
    if instance.pk:
        old_cover = (
            Collect.objects.filter(pk=instance.pk)
            .values_list("cover", flat=True)
            .first()
        )
        if old_cover != new_cover_name:
            process_cover_image(instance)
    else:
        process_cover_image(instance)
