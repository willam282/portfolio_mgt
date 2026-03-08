from django.db import models
from django.urls import reverse


class Asset(models.Model):
    ASSET_TYPES = [
        ("STOCK", "Stock"),
        ("ETF", "ETF"),
        ("CRYPTO", "Cryptocurrency"),
        ("BOND", "Bond"),
        ("COMMODITY", "Commodity"),
    ]

    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, default="STOCK")
    current_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol} - {self.name}"

    @classmethod
    def update_prices(cls):
        import yfinance as yf
        from datetime import datetime, timedelta
        import pandas as pd

        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)

        for asset in cls.objects.all():
            try:
                yf_symbol = asset.symbol.upper()
                if '/USD' in yf_symbol:
                    yf_symbol = yf_symbol.replace('/USD', '-USD')
                elif asset.asset_type == 'CRYPTO' and not yf_symbol.endswith('-USD'):
                    yf_symbol = f"{yf_symbol}-USD"
                elif yf_symbol in ['BTC', 'ETH', 'SOL', 'ADA', 'XRP', 'DOGE', 'DOT', 'LTC']:
                    yf_symbol = f"{yf_symbol}-USD"

                data = yf.download(yf_symbol, start=start_date, end=end_date, interval='1d', auto_adjust=True, actions=True, progress=False)
                if not data.empty and 'Close' in data:
                    # yfinance returns a DataFrame; get the last available 'Close' price
                    last_price = data['Close'].dropna().iloc[-1]
                    if isinstance(last_price, pd.Series): # Handle MultiIndex returning Series
                        last_price = float(last_price.iloc[0])
                    asset.current_price = float(last_price)
                    asset.save(update_fields=['current_price'])
            except Exception as e:
                print(f"Error fetching price for {asset.symbol}: {e}")


class Portfolio(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "portfolios"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("portfolio_detail", kwargs={"pk": self.pk})

    @property
    def total_value(self):
        """Calculate current total value of all holdings."""
        total = 0.0
        for holding in self.get_holdings():
            total += holding["market_value"]
        return total

    @property
    def total_cost(self):
        """Calculate total cost basis including commissions."""
        buys = self.transactions.filter(transaction_type="BUY")
        total = sum(float(t.quantity * t.price) + float(t.commission) for t in buys)
        sells = self.transactions.filter(transaction_type="SELL")
        total -= sum(float(t.quantity * t.price) - float(t.commission) for t in sells)
        return total

    @property
    def total_gain_loss(self):
        return self.total_value - self.total_cost

    @property
    def gain_loss_sign(self):
        gain = self.total_gain_loss
        return "-$" if gain < 0 else ("+$" if gain > 0 else "$")

    @property
    def gain_loss_pct_sign(self):
        gain = self.total_gain_loss
        return "-" if gain < 0 else ("+" if gain > 0 else "")

    @property
    def total_gain_loss_pct(self):
        cost = self.total_cost
        if cost == 0:
            return 0
        return ((self.total_value - cost) / cost) * 100

    def get_holdings(self):
        """Get current holdings grouped by asset."""
        from django.db.models import Sum, Q

        holdings = []
        assets = Asset.objects.filter(
            transactions__portfolio=self
        ).distinct()

        for asset in assets:
            bought = (
                self.transactions.filter(asset=asset, transaction_type="BUY")
                .aggregate(total=Sum("quantity"))["total"]
                or 0
            )
            sold = (
                self.transactions.filter(asset=asset, transaction_type="SELL")
                .aggregate(total=Sum("quantity"))["total"]
                or 0
            )
            qty = bought - sold
            # Calculate average cost
            buys = self.transactions.filter(asset=asset, transaction_type="BUY")
            total_buy_cost = sum(float(t.quantity * t.price) + float(t.commission) for t in buys)
            total_buy_qty = sum(float(t.quantity) for t in buys)
            avg_cost = total_buy_cost / total_buy_qty if total_buy_qty > 0 else 0

            if qty > 0:
                market_value = float(qty) * float(asset.current_price)
                cost_basis = float(qty) * avg_cost
                gain_loss = market_value - cost_basis
                holdings.append(
                    {
                        "asset": asset,
                        "quantity": float(qty),
                        "current_price": float(asset.current_price),
                        "market_value": market_value,
                        "avg_cost": avg_cost,
                        "cost_basis": cost_basis,
                        "gain_loss": gain_loss,
                        "gain_loss_pct": (gain_loss / cost_basis * 100) if cost_basis else 0,
                    }
                )
        return holdings


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
    ]

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="transactions"
    )
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date = models.DateField()
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.asset.symbol} @ {self.price}"

    @property
    def total_amount(self):
        if self.transaction_type == "BUY":
            return (self.quantity * self.price) + self.commission
        else:
            return (self.quantity * self.price) - self.commission


class PortfolioSnapshot(models.Model):
    """Daily snapshot of portfolio value for charting."""

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="snapshots"
    )
    date = models.DateField()
    total_value = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ["date"]
        unique_together = ["portfolio", "date"]

    def __str__(self):
        return f"{self.portfolio.name} - {self.date}: ${self.total_value}"
