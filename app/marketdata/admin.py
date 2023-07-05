from django.contrib import admin
from .models import *


@admin.action(description="Atualizar Cotações")
def atualizar_cotacoes(modeladmin, request, queryset):
    [asset.update_quotes(num_bars=1000) for asset in queryset]


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ["ticker", "name"]
    search_fields = ["ticker", "name"]

    actions = [atualizar_cotacoes]


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["date", "symbol", "open", "high", "low", "close", "volume"]
    search_fields = ["symbol__ticker", "symbol__name"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "yahoo_suffix"]


admin.site.register(Broker)
