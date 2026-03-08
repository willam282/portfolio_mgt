import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum

from .models import Asset, Portfolio, Transaction, PortfolioSnapshot
from .forms import PortfolioForm, TransactionForm


# ─── Dashboard ────────────────────────────────────────────────────────

def dashboard(request):
    portfolios = Portfolio.objects.all()
    recent_transactions = Transaction.objects.select_related("portfolio", "asset")[:10]

    # Aggregate summary
    total_value = sum(p.total_value for p in portfolios)
    total_cost = sum(p.total_cost for p in portfolios)
    total_gain = total_value - total_cost
    gain_pct = ((total_gain / total_cost) * 100) if total_cost else 0
    total_assets = Asset.objects.filter(transactions__isnull=False).distinct().count()

    context = {
        "portfolios": portfolios,
        "recent_transactions": recent_transactions,
        "total_value": total_value,
        "total_cost": total_cost,
        "total_gain": total_gain,
        "gain_sign": "-$" if total_gain < 0 else ("+$" if total_gain > 0 else "$"),
        "gain_pct": gain_pct,
        "total_assets": total_assets,
        "portfolio_count": portfolios.count(),
    }
    return render(request, "dashboard.html", context)


# ─── Portfolio CRUD ───────────────────────────────────────────────────

def portfolio_list(request):
    portfolios = Portfolio.objects.all()
    return render(request, "portfolio_list.html", {"portfolios": portfolios})


def portfolio_detail(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk)
    holdings = portfolio.get_holdings()
    transactions = portfolio.transactions.select_related("asset")[:20]
    context = {
        "portfolio": portfolio,
        "holdings": holdings,
        "transactions": transactions,
    }
    return render(request, "portfolio_detail.html", context)


def portfolio_create(request):
    if request.method == "POST":
        form = PortfolioForm(request.POST)
        if form.is_valid():
            portfolio = form.save()
            messages.success(request, f'Portfolio "{portfolio.name}" created successfully!')
            return redirect("portfolio_detail", pk=portfolio.pk)
    else:
        form = PortfolioForm()
    return render(request, "portfolio_form.html", {"form": form, "title": "Create Portfolio"})


def portfolio_edit(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk)
    if request.method == "POST":
        form = PortfolioForm(request.POST, instance=portfolio)
        if form.is_valid():
            form.save()
            messages.success(request, f'Portfolio "{portfolio.name}" updated successfully!')
            return redirect("portfolio_detail", pk=portfolio.pk)
    else:
        form = PortfolioForm(instance=portfolio)
    return render(request, "portfolio_form.html", {"form": form, "title": "Edit Portfolio"})


def portfolio_delete(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk)
    if request.method == "POST":
        name = portfolio.name
        portfolio.delete()
        messages.success(request, f'Portfolio "{name}" deleted.')
        return redirect("portfolio_list")
    return render(request, "portfolio_confirm_delete.html", {"portfolio": portfolio})


# ─── Transaction CRUD ─────────────────────────────────────────────────

def transaction_list(request):
    transactions = Transaction.objects.select_related("portfolio", "asset")
    return render(request, "transaction_list.html", {"transactions": transactions})


def transaction_add(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            txn = form.save()
            messages.success(
                request,
                f'{txn.transaction_type} {txn.quantity} {txn.asset.symbol} recorded!'
            )
            return redirect("transaction_list")
    else:
        form = TransactionForm()
    return render(request, "transaction_form.html", {"form": form, "title": "Add Transaction"})


# ─── API Endpoints (JSON for Chart.js) ────────────────────────────────

def api_portfolio_history(request, pk):
    """Return JSON with date + value arrays for the portfolio growth chart."""
    snapshots = PortfolioSnapshot.objects.filter(portfolio_id=pk).order_by("date")
    data = {
        "labels": [s.date.strftime("%Y-%m-%d") for s in snapshots],
        "values": [float(s.total_value) for s in snapshots],
    }
    return JsonResponse(data)


def api_allocation(request, pk):
    """Return JSON with asset allocation breakdown for doughnut chart."""
    portfolio = get_object_or_404(Portfolio, pk=pk)
    holdings = portfolio.get_holdings()
    data = {
        "labels": [h["asset"].symbol for h in holdings],
        "values": [h["market_value"] for h in holdings],
    }
    return JsonResponse(data)


def api_all_portfolios_history(request):
    """Aggregated history across all portfolios for dashboard chart."""
    from collections import defaultdict

    combined = defaultdict(float)
    snapshots = PortfolioSnapshot.objects.all().order_by("date")
    for s in snapshots:
        combined[s.date.strftime("%Y-%m-%d")] += float(s.total_value)

    sorted_dates = sorted(combined.keys())
    data = {
        "labels": sorted_dates,
        "values": [combined[d] for d in sorted_dates],
    }
    return JsonResponse(data)


def api_all_allocation(request):
    """Aggregated asset allocation across all portfolios."""
    from collections import defaultdict

    allocation = defaultdict(float)
    for portfolio in Portfolio.objects.all():
        for h in portfolio.get_holdings():
            allocation[h["asset"].symbol] += h["market_value"]

    data = {
        "labels": list(allocation.keys()),
        "values": list(allocation.values()),
    }
    return JsonResponse(data)
