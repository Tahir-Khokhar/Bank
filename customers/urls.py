from django.urls import path

from .views import CustomerLoginView, CustomerRegisterView


urlpatterns = [
    path('customers/login/', CustomerLoginView.as_view(), name='customer-login'),
    path('customers/register', CustomerRegisterView.as_view(), name='customer-register'),
]

