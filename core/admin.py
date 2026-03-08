from django.contrib import admin
from .models import Asset, Portfolio, Transaction, PortfolioSnapshot


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["symbol", "name", "asset_type", "current_price"]
    list_filter = ["asset_type"]
    search_fields = ["symbol", "name"]


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at", "updated_at"]
    search_fields = ["name"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["portfolio", "asset", "transaction_type", "quantity", "price", "date"]
    list_filter = ["transaction_type", "portfolio", "date"]
    search_fields = ["asset__symbol", "asset__name"]


@admin.register(PortfolioSnapshot)
class PortfolioSnapshotAdmin(admin.ModelAdmin):
    list_display = ["portfolio", "date", "total_value"]
    list_filter = ["portfolio", "date"]
