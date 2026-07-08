from django.urls import path

from .views import EmployeeLoginView, EmployeeRegisterView


urlpatterns = [
    path('login/', EmployeeLoginView.as_view(), name='employee-login'),
    path('register/', EmployeeRegisterView.as_view(), name='employee-register'),
]

