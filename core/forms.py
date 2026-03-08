from django import forms
from .models import Portfolio, Transaction


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Retirement Fund",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Brief description of this portfolio...",
                }
            ),
        }


class TransactionForm(forms.ModelForm):
    asset_symbol = forms.CharField(
        max_length=20,
        required=True,
        label="Asset Symbol",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. AAPL, BTC"})
    )
    asset_name = forms.CharField(
        max_length=200,
        required=False,
        label="Asset Name (optional)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Apple Inc."})
    )

    class Meta:
        model = Transaction
        fields = ["portfolio", "transaction_type", "quantity", "price", "commission", "date", "notes"]
        widgets = {
            "portfolio": forms.Select(attrs={"class": "form-select"}),
            "transaction_type": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.0001", "placeholder": "0.00", "id": "id_quantity"}
            ),
            "price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}
            ),
            "commission": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00", "id": "id_commission"}
            ),
            "date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": "Optional notes..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.asset:
            self.fields["asset_symbol"].initial = self.instance.asset.symbol
            self.fields["asset_name"].initial = self.instance.asset.name

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity")
        commission = cleaned_data.get("commission")

        # Automatically sets commission if it is blank, 0, or one of the auto-calculated values
        if quantity is not None:
            comm_val = float(commission) if commission is not None else 0.0
            if comm_val in (0.0, 20.00, 0.88):
                if quantity >= 1:
                    cleaned_data["commission"] = 20.00
                else:
                    cleaned_data["commission"] = 0.88
        
        return cleaned_data

    def save(self, commit=True):
        from .models import Asset
        instance = super().save(commit=False)
        symbol = self.cleaned_data.get("asset_symbol").upper()
        name = self.cleaned_data.get("asset_name") or symbol

        asset, created = Asset.objects.get_or_create(
            symbol=symbol,
            defaults={"name": name, "current_price": instance.price}
        )
        
        # Update current price from Yahoo Finance
        try:
            import yfinance as yf
            from datetime import datetime, timedelta
            import pandas as pd
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5)
            # Use user's requested syntax for yf download
            yf_symbol = symbol.upper()
            if '/USD' in yf_symbol:
                yf_symbol = yf_symbol.replace('/USD', '-USD')
            elif asset.asset_type == 'CRYPTO' and not yf_symbol.endswith('-USD'):
                yf_symbol = f"{yf_symbol}-USD"
            elif yf_symbol in ['BTC', 'ETH', 'SOL', 'ADA', 'XRP', 'DOGE', 'DOT', 'LTC']:
                yf_symbol = f"{yf_symbol}-USD"
                
            data = yf.download(yf_symbol, start=start_date, end=end_date, interval='1d', auto_adjust=True, actions=True, progress=False)
            if not data.empty and 'Close' in data:
                last_price = data['Close'].dropna().iloc[-1]
                if isinstance(last_price, pd.Series):
                    last_price = float(last_price.iloc[0])
                asset.current_price = float(last_price)
                asset.save(update_fields=["current_price"])
        except Exception as e:
            # Fallback to the transaction price if completely failed
            pass


        instance.asset = asset
        instance.commission = self.cleaned_data.get("commission", 0.0)
        
        if commit:
            instance.save()
        return instance
