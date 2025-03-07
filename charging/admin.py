from django.contrib import admin

from charging.models import Charger, Transaction

# Register your models here.
@admin.register(Charger)
class ChargerAdmin(admin.ModelAdmin):
    list_display = ("charger_id", "model", "vendor", "last_seen")

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "charger", "user_id_tag", "start_time", "stop_time", "energy_consumed")
    list_filter = ("charger", "start_time", "stop_time")
    search_fields = ("transaction_id", "charger__charger_id", "user_id_tag")
    date_hierarchy = "start_time"
