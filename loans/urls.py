from django.urls import path

from .views import (
    LoanApplyView,
    LoanDecisionView,
    LoanDetailView,
    LoanListView,
    LoanRepaymentView,
)


urlpatterns = [
    path("", LoanListView.as_view(), name="loan-list"),
    path("apply/", LoanApplyView.as_view(), name="loan-apply"),
    path("<int:pk>/", LoanDetailView.as_view(), name="loan-detail"),
    path("<int:pk>/decision/", LoanDecisionView.as_view(), name="loan-decision"),
    path("<int:pk>/repay/", LoanRepaymentView.as_view(), name="loan-repay"),
]
