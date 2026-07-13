from django.urls import path

from .views import (
    CustomerReportView,
    LoanReportView,
    ReportsHomeView,
    StatementReportView,
    TransactionReportView,
)


urlpatterns = [
    path("", ReportsHomeView.as_view(), name="reports-home"),
    path("statement/", StatementReportView.as_view(), name="report-statement"),
    path("transactions/", TransactionReportView.as_view(), name="report-transactions"),
    path("customers/", CustomerReportView.as_view(), name="report-customers"),
    path("loans/", LoanReportView.as_view(), name="report-loans"),
]
