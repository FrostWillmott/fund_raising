from django.db.models.signals import pre_save
from django.dispatch import receiver
from collects.models import Collect
from collects.utils import process_cover_image

@receiver(pre_save, sender=Collect)
def handle_cover_image(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Collect.objects.get(pk=instance.pk)
            if old_instance.cover != instance.cover:
                process_cover_image(instance)
        except Collect.DoesNotExist:
            process_cover_image(instance)
    else:
        process_cover_image(instance)