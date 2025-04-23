from django.contrib import admin

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    search_fields = ["collect__title", "transaction_id", "payer__username", "payer__email"]
    list_display = ["status", "payer", "collect", "amount", "transaction_id", "payment_date"]
    list_filter = ["status", "payment_date"]
