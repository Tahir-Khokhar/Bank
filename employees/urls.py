from django.urls import path

from .views import EmployeeLoginView, EmployeeRegisterView


urlpatterns = [
    path('employees/login/', EmployeeLoginView.as_view(), name='employee-login'),
    path('employees/register/', EmployeeRegisterView.as_view(), name='employee-register'),
]

