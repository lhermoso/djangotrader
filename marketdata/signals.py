from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Symbol


@receiver(post_save, sender=Symbol)
def update_broker(sender, instance, created, *args, **kwargs):
    if created:
        try:
            instance.update_broker()
        except KeyError:
            pass
