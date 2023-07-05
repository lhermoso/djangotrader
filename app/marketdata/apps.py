from django.apps import AppConfig


class MarketdataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'marketdata'

    def ready(self):
        import marketdata.signals
