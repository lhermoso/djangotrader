from django.contrib import admin
from .models import *


# Register your models here.


class AccountInline(admin.StackedInline):
    model = Account
    extra = 0


@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ["name"]
    inlines = [AccountInline]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["broker", "account", "user", "server"]
    search_fields = ["account", "user"]


