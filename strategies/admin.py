from django.contrib import admin
from .models import *


# Register your models here.


@admin.register(Timeframe)
class TimeframeAdmin(admin.ModelAdmin):
    list_display = ["full_name", "name"]


@admin.register(Volatility)
class VolatilityAdmin(admin.ModelAdmin):
    list_display = ["symbol", "log_periods", "trigger","sharpe","factor","signal"]
