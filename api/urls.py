from django.urls import path  # Imports the function for defining URL routes.

from .views import (  # Imports API views for employees and customers.
    CustomerListAPIView,
    EmployeeListAPIView,
)


app_name = "api"  # Defines the application namespace for URL names.

urlpatterns = [  # Maps API endpoints to their corresponding views.
    path("employees/", EmployeeListAPIView.as_view(), name="employee-list"),
    path("customers/", CustomerListAPIView.as_view(), name="customer-list"),
]
