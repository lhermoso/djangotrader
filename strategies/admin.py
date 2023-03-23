from django.contrib import admin
from .models import *


# Register your models here.


class ParamsInline(admin.TabularInline):
    model = Param
    extra = 0


class PlayersInline(admin.TabularInline):
    model = Player
    extra = 0


@admin.register(Timeframe)
class TimeframeAdmin(admin.ModelAdmin):
    list_display = ["full_name", "name"]


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ["name", "enabled"]
    inlines = [PlayersInline]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ["strategy", "symbol", "sharpe", "factor", "signal","enabled"]
    list_filter = ["strategy"]
    inlines = [ParamsInline]
