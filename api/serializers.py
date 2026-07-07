from __future__ import annotations

from rest_framework import serializers

from employees.models import Employee
from customers.models import Customer


class EmployeeRegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value: str) -> str:
        if Employee.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value: str) -> str:
        if Employee.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered for an employee.")
        return value

    def create(self, validated_data: dict) -> Employee:
        employee = Employee(
            full_name=validated_data["full_name"],
            username=validated_data["username"],
            email=validated_data["email"],
        )
        employee.set_password(validated_data["password"])
        employee.save()
        return employee


class EmployeeLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        username = attrs.get("username")
        password = attrs.get("password")

        try:
            employee = Employee.objects.get(username=username, is_active=True)
        except Employee.DoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid username or password."]}
            )

        if not employee.check_password(password):
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid username or password."]}
            )

        attrs["employee"] = employee
        return attrs


class CustomerRegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value: str) -> str:
        if Customer.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value: str) -> str:
        if Customer.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered for a customer.")
        return value

    def create(self, validated_data: dict) -> Customer:
        customer = Customer(
            full_name=validated_data["full_name"],
            username=validated_data["username"],
            email=validated_data["email"],
        )
        customer.set_password(validated_data["password"])
        customer.save()
        return customer


class CustomerLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        username = attrs.get("username")
        password = attrs.get("password")

        try:
            customer = Customer.objects.get(username=username, is_active=True)
        except Customer.DoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid username or password."]}
            )

        if not customer.check_password(password):
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid username or password."]}
            )

        attrs["customer"] = customer
        return attrs

