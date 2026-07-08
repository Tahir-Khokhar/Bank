from __future__ import annotations

from rest_framework import serializers

from employees.models import Employee
from customers.models import Customer


class EmployeeRegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)  # Accept full name
    username = serializers.CharField(max_length=150)  # Accept username
    email = serializers.EmailField()  # Accept email
    password = serializers.CharField(write_only=True, min_length=8)  # Accept password

    def validate_username(self, value: str) -> str:  # Validate username
        if Employee.objects.filter(username=value).exists():  # Filter matching username
            raise serializers.ValidationError("This username is already taken.")  # Raise validation error
        return value  # Return valid username

    def validate_email(self, value: str) -> str:  # Validate email
        if Employee.objects.filter(email=value).exists():  # Filter matching email
            raise serializers.ValidationError("This email is already registered for an employee.")  # Raise validation error
        return value  # Return valid email

    def create(self, validated_data: dict) -> Employee:  # Create employee
        employee = Employee(
            full_name=validated_data["full_name"],
            username=validated_data["username"],
            email=validated_data["email"],
        )
        employee.set_password(validated_data["password"])  # Hash password
        employee.save()  # Save employee
        return employee  # Return employee


class EmployeeLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)  # Accept username
    password = serializers.CharField(write_only=True)  # Accept password

    def validate(self, attrs: dict) -> dict:  # Validate login
        username = attrs.get("username")  # Get username
        password = attrs.get("password")  # Get password

        try:
            employee = Employee.objects.get(username=username, is_active=True)  # Get active employee
        except Employee.DoesNotExist:
            raise serializers.ValidationError(  # Raise validation error
                {"non_field_errors": ["Invalid username or password."]}
            )

        if not employee.check_password(password):  # Check password
            raise serializers.ValidationError(  # Raise validation error
                {"non_field_errors": ["Invalid username or password."]}
            )

        attrs["employee"] = employee  # Store employee
        return attrs  # Return validated data


class CustomerRegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)  # Accept full name
    username = serializers.CharField(max_length=150)  # Accept username
    email = serializers.EmailField()  # Accept email
    password = serializers.CharField(write_only=True, min_length=8)  # Accept password

    def validate_username(self, value: str) -> str:  # Validate username
        if Customer.objects.filter(username=value).exists():  # Filter matching username
            raise serializers.ValidationError("This username is already taken.")  # Raise validation error
        return value  # Return valid username

    def validate_email(self, value: str) -> str:  # Validate email
        if Customer.objects.filter(email=value).exists():  # Filter matching email
            raise serializers.ValidationError("This email is already registered for a customer.")  # Raise validation error
        return value  # Return valid email

    def create(self, validated_data: dict) -> Customer:  # Create customer
        customer = Customer(
            full_name=validated_data["full_name"],
            username=validated_data["username"],
            email=validated_data["email"],
        )
        customer.set_password(validated_data["password"])  # Hash password
        customer.save()  # Save customer
        return customer  # Return customer


class CustomerLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)  # Accept username
    password = serializers.CharField(write_only=True)  # Accept password

    def validate(self, attrs: dict) -> dict:  # Validate login
        username = attrs.get("username")  # Get username
        password = attrs.get("password")  # Get password

        try:
            customer = Customer.objects.get(username=username, is_active=True)  # Get active customer
        except Customer.DoesNotExist:
            raise serializers.ValidationError(  # Raise validation error
                {"non_field_errors": ["Invalid username or password."]}
            )

        if not customer.check_password(password):  # Check password
            raise serializers.ValidationError(  # Raise validation error
                {"non_field_errors": ["Invalid username or password."]}
            )

        attrs["customer"] = customer  # Store customer
        return attrs  # Return validated data
