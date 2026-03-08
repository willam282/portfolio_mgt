from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Portfolios
    path("portfolios/", views.portfolio_list, name="portfolio_list"),
    path("portfolios/new/", views.portfolio_create, name="portfolio_create"),
    path("portfolios/<int:pk>/", views.portfolio_detail, name="portfolio_detail"),
    path("portfolios/<int:pk>/edit/", views.portfolio_edit, name="portfolio_edit"),
    path("portfolios/<int:pk>/delete/", views.portfolio_delete, name="portfolio_delete"),

    # Transactions
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/new/", views.transaction_add, name="transaction_add"),

    # API (JSON for charts)
    path("api/portfolio/<int:pk>/history/", views.api_portfolio_history, name="api_portfolio_history"),
    path("api/portfolio/<int:pk>/allocation/", views.api_allocation, name="api_allocation"),
    path("api/portfolios/history/", views.api_all_portfolios_history, name="api_all_portfolios_history"),
    path("api/portfolios/allocation/", views.api_all_allocation, name="api_all_allocation"),
]
