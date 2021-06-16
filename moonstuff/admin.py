from django.contrib import admin

from .models import Extraction, Refinery, TrackingCharacter


# Register your models here.
class TrackingCharacterAdmin(admin.ModelAdmin):
    list_display = ("character",
                    "get_corp",
                    "latest_notification_id",
                    "last_notification_check")

    def get_corp(self, obj):
        return obj.character.corporation_name

    get_corp.short_description = "Corporation"
    get_corp.admin_order_field = "character__corporation_name"

    list_filter = ("character__corporation_name",)
    search_fields = ("character__corporation_name", "character__character_name")


class ExtractionAdmin(admin.ModelAdmin):
    list_select_related = True
    list_display = ("moon",
                    "refinery",
                    "corp",
                    "cancelled",
                    "start_time",
                    "arrival_time",
                    "total_volume",
                    "decay_time",
                    "despawn",
                    "active",
                    "jackpot",
                    "depleted")

    list_filter = ("moon", "corp", "refinery", "jackpot", "cancelled", "active")
    search_fields = ("corp__corporation_name", "moon__name", "refinery__name")


admin.site.register(Extraction, ExtractionAdmin)
admin.site.register(TrackingCharacter, TrackingCharacterAdmin)
