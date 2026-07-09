
from __future__ import annotations

from django.urls import path

from dashboard.views import AdminDashboardView, CustomerDashboardView, EmployeeDashboardView


urlpatterns = [
    path('admin/', AdminDashboardView.as_view(), name='dashboard-admin'),
    path('employee/', EmployeeDashboardView.as_view(), name='dashboard-employee'),
    path('customer/', CustomerDashboardView.as_view(), name='dashboard-customer'),
]

