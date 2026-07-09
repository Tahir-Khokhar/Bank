from __future__ import annotations

from rest_framework import serializers

from employees.models import Employee
from customers.models import Customer


class EmployeeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = "__all__"


class CustomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"

