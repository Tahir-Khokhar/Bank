from django.urls import path

from .views import (
    DepositView,
    ReverseTransactionView,
    TransactionDetailView,
    TransactionExportView,
    TransactionListView,
    TransferView,
    WithdrawView,
)


urlpatterns = [
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("deposit/", DepositView.as_view(), name="transaction-deposit"),
    path("withdraw/", WithdrawView.as_view(), name="transaction-withdraw"),
    path("transfer/", TransferView.as_view(), name="transaction-transfer"),
    path("export/<str:fmt>/", TransactionExportView.as_view(), name="transaction-export"),
    path("<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path("<int:pk>/reverse/", ReverseTransactionView.as_view(), name="transaction-reverse"),
]
