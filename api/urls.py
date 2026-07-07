from django.urls import path

from .views import (
    CustomerLoginAPIView,
    CustomerRegisterAPIView,
    EmployeeLoginAPIView,
    EmployeeRegisterAPIView,
)

urlpatterns = [
    path("employees/register/", EmployeeRegisterAPIView.as_view(), name="employee-register"),
    path("employees/login/", EmployeeLoginAPIView.as_view(), name="employee-login"),
    path("customers/register/", CustomerRegisterAPIView.as_view(), name="customer-register"),
    path("customers/login/", CustomerLoginAPIView.as_view(), name="customer-login"),
]

