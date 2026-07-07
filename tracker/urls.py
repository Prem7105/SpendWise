from django.urls import path
from . import views

urlpatterns = [
    path("",views.dashboard,name="dashboard"),
    path("income/",views.transaction_list,{"txn_type":"INCOME"},name="income"),
    path("expense/",views.transaction_list,{"txn_type":"EXPENSE"},name="expense"),
    path("transactions/add/<str:txn_type>/",views.transaction_create,name="transaction_create"),
    path("transactions/<int:pk>/edit/",views.transaction_update,name="transaction_update"),
    path("transactions/<int:pk>/delete/",views.category_delete,name="transaction_delete"),
    path("categories/",views.category_list,name="category_list"),
    path("categories/<int:pk>/edit/",views.category_update,name="category_update"),
    path("categories/<int:pk>/delete/",views.category_delete,name="category_delete"),
    path("reports/",views.reports,name="reports"),
    path("exports/csv/",views.export_csv,name="export_csv"),
    path("profile/",views.profile,name="profile"),
]