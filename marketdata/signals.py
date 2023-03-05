from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Symbol


@receiver(post_save, sender=Symbol)
def update_broker(sender, instance, created, *args, **kwargs):
    if created:
        try:
            instance.update_broker()
        except KeyError:
            pass


@receiver(pre_save, sender=Symbol)
def capitalize_symbol_ticker(sender, instance, *args, **kwargs):
    instance.ticker = instance.ticker.upper()
