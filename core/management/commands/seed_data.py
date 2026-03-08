import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from core.models import Asset, Portfolio, Transaction, PortfolioSnapshot


class Command(BaseCommand):
    help = "Seed the database with sample portfolio data for demonstration"

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        # ── Assets ────────────────────────────────────────────────────
        assets_data = [
            ("AAPL",  "Apple Inc.",           "STOCK",  189.84),
            ("MSFT",  "Microsoft Corp.",      "STOCK",  417.88),
            ("GOOGL", "Alphabet Inc.",        "STOCK",  174.79),
            ("AMZN",  "Amazon.com Inc.",      "STOCK",  200.41),
            ("TSLA",  "Tesla Inc.",           "STOCK",  175.21),
            ("NVDA",  "NVIDIA Corp.",         "STOCK",  131.60),
            ("VLO",   "Valero Energy Corp",   "STOCK",  140.50),
            ("BTC",   "Bitcoin",              "CRYPTO", 97245.00),
            ("ETH",   "Ethereum",             "CRYPTO", 3315.50),
            ("VOO",   "Vanguard S&P 500 ETF", "ETF",   527.35),
            ("QQQ",   "Invesco QQQ Trust",    "ETF",    518.46),
            ("IVV",   "iShares Core S&P 500", "ETF",    535.10),
            ("GLD",   "SPDR Gold Shares",     "COMMODITY", 236.12),
            ("IAU",   "iShares Gold Trust",   "COMMODITY", 46.20),
            ("SLV",   "iShares Silver Trust", "COMMODITY", 28.50),
        ]

        assets = {}
        for symbol, name, asset_type, price in assets_data:
            asset, created = Asset.objects.update_or_create(
                symbol=symbol,
                defaults={"name": name, "asset_type": asset_type, "current_price": Decimal(str(price))},
            )
            assets[symbol] = asset
            status = "Created" if created else "Updated"
            self.stdout.write(f"  {status} asset: {symbol}")

        # ── Portfolios ────────────────────────────────────────────────
        p1, _ = Portfolio.objects.get_or_create(
            name="Growth Portfolio",
            defaults={"description": "High-growth tech stocks and crypto with long-term horizon."},
        )
        p2, _ = Portfolio.objects.get_or_create(
            name="Dividend Income",
            defaults={"description": "Stable ETFs and blue-chip stocks for dividend income."},
        )
        p3, _ = Portfolio.objects.get_or_create(
            name="Crypto Fund",
            defaults={"description": "Bitcoin, Ethereum, and experimental crypto positions."},
        )
        self.stdout.write(f"  Portfolios ready: {p1.name}, {p2.name}, {p3.name}")

        # ── Transactions ──────────────────────────────────────────────
        if Transaction.objects.exists():
            self.stdout.write("  Transactions already exist — skipping.")
        else:
            today = date.today()
            transactions = [
                # Growth Portfolio
                (p1, "AAPL",  "BUY",  50, 142.50, today - timedelta(days=180)),
                (p1, "MSFT",  "BUY",  30, 350.20, today - timedelta(days=170)),
                (p1, "NVDA",  "BUY",  80, 88.40,  today - timedelta(days=160)),
                (p1, "TSLA",  "BUY",  25, 190.00, today - timedelta(days=150)),
                (p1, "GOOGL", "BUY",  40, 155.30, today - timedelta(days=140)),
                (p1, "TSLA",  "SELL", 10, 210.50, today - timedelta(days=60)),
                (p1, "NVDA",  "BUY",  20, 120.00, today - timedelta(days=30)),

                # Dividend Income
                (p2, "VOO",   "BUY",  100, 470.00, today - timedelta(days=200)),
                (p2, "QQQ",   "BUY",  60,  480.25, today - timedelta(days=190)),
                (p2, "AAPL",  "BUY",  30,  150.00, today - timedelta(days=160)),
                (p2, "GLD",   "BUY",  45,  215.80, today - timedelta(days=120)),
                (p2, "VOO",   "BUY",  20,  510.30, today - timedelta(days=40)),

                # Crypto Fund
                (p3, "BTC",   "BUY",  0.5,  62400.00, today - timedelta(days=220)),
                (p3, "ETH",   "BUY",  8,    2850.00,  today - timedelta(days=210)),
                (p3, "BTC",   "BUY",  0.3,  71200.00, today - timedelta(days=100)),
                (p3, "ETH",   "BUY",  5,    3100.00,  today - timedelta(days=80)),
                (p3, "BTC",   "SELL", 0.1,  94500.00, today - timedelta(days=20)),
            ]

            for portfolio, symbol, txn_type, qty, price, txn_date in transactions:
                Transaction.objects.create(
                    portfolio=portfolio,
                    asset=assets[symbol],
                    transaction_type=txn_type,
                    quantity=Decimal(str(qty)),
                    price=Decimal(str(price)),
                    date=txn_date,
                )
            self.stdout.write(f"  Created {len(transactions)} transactions.")

        # ── Portfolio Snapshots (simulated history) ────────────────────
        if PortfolioSnapshot.objects.exists():
            self.stdout.write("  Snapshots already exist — skipping.")
        else:
            self._generate_snapshots(p1, base_value=35000, days=180)
            self._generate_snapshots(p2, base_value=80000, days=200)
            self._generate_snapshots(p3, base_value=55000, days=220)
            self.stdout.write("  Generated portfolio snapshots.")

        self.stdout.write(self.style.SUCCESS("\nDone! Visit http://127.0.0.1:8000/ to see your dashboard."))

    def _generate_snapshots(self, portfolio, base_value, days):
        """Generate realistic-ish daily portfolio value snapshots."""
        today = date.today()
        value = float(base_value)
        snapshots = []

        for i in range(days, -1, -1):
            # Random daily return between -2% and +2.5% (slight upward bias)
            daily_return = random.gauss(0.0008, 0.012)
            value *= (1 + daily_return)
            value = max(value, base_value * 0.5)  # floor at 50% of base

            snapshots.append(
                PortfolioSnapshot(
                    portfolio=portfolio,
                    date=today - timedelta(days=i),
                    total_value=Decimal(str(round(value, 2))),
                )
            )

        PortfolioSnapshot.objects.bulk_create(snapshots, ignore_conflicts=True)
