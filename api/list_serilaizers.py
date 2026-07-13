from __future__ import annotations  # Enables postponed evaluation of type annotations.

from rest_framework import serializers  # Imports serializer classes for converting model data.

from employees.models import Employee  # Imports the Employee model.
from customers.models import Customer  # Imports the Customer model.


class EmployeeListSerializer(serializers.ModelSerializer):  # Serializes all Employee model fields.
    class Meta:  # Configures serializer options.
        model = Employee
        fields = "__all__"


class CustomerListSerializer(serializers.ModelSerializer):  # Serializes all Customer model fields.
    class Meta:  # Configures serializer options.
        model = Customer
        fields = "__all__"
