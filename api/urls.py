from django.urls import path

from .views import (
    CustomerListAPIView,
    EmployeeListAPIView,

)


app_name = "api"

urlpatterns = [
    path("employees/", EmployeeListAPIView.as_view(), name="employee-list"),
    path("customers/", CustomerListAPIView.as_view(), name="customer-list"),
    
]





