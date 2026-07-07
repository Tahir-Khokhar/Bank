from django.urls import path

from .views import CustomerLoginView, CustomerRegisterView


urlpatterns = [
    path('login/', CustomerLoginView.as_view(), name='customer-login'),
    path('register/', CustomerRegisterView.as_view(), name='customer-register'),
]

