from django.contrib import admin
from .models import *


# Register your models here.

@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ["ticker", "name"]
    search_fields = ["ticker", "name"]


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["date", "symbol", "open", "high", "low", "close", "volume"]
    search_fields = ["symbol__ticker", "symbol__name"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "yahoo_suffix"]


admin.site.register(Broker)
