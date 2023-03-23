from django.core.management.base import BaseCommand

try:
    from strategies.volatility import Volatility
except:
    from strategies.volatility import Volatility

import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)


class Command(BaseCommand):
    def handle(self, *args, **options):
        vol = Volatility(account=1571013)
        input("Done! Press enter key to exit\n")



