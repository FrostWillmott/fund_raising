from django.contrib import admin

from collects.models import Collect


@admin.register(Collect)
class CollectAdmin(admin.ModelAdmin):
    search_fields = ["title", "description", "occasion"]
    list_display = ["title", "description", "created_by", "goal_amount", "created_at",
                    "is_active", "start_date", "end_date", "occasion", "collected_amount"]
    list_filter = ["is_active", "occasion", "start_date", "end_date"]
