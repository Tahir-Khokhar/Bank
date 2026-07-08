from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    CustomerLoginSerializer,
    CustomerRegisterSerializer,
    EmployeeLoginSerializer,
    EmployeeRegisterSerializer,
)


def _build_tokens(*, user_id: int, role: str) -> dict:  # Create JWT tokens
    """Create refresh/access tokens with role + user_id claims."""
    refresh = RefreshToken()  # Create refresh token
    refresh["role"] = role  # Add user role
    refresh["user_id"] = user_id  # Add user ID

    return {"access": str(refresh.access_token), "refresh": str(refresh)}  # Return access and refresh tokens


class EmployeeRegisterAPIView(APIView):
    authentication_classes = []  # No authentication required
    permission_classes = []  # Allow all users

    def post(self, request):
        serializer = EmployeeRegisterSerializer(data=request.data)  # Load request data
        serializer.is_valid(raise_exception=True)  # Validate input data
        employee = serializer.save()  # Save employee
        return Response(  # Return success response
            {"message": "Employee registered successfully.", "id": employee.id},
            status=status.HTTP_201_CREATED,  # Return HTTP 201 status
        )


class CustomerRegisterAPIView(APIView):
    authentication_classes = []  # No authentication required
    permission_classes = []  # Allow all users

    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)  # Load request data
        serializer.is_valid(raise_exception=True)  # Validate input data
        customer = serializer.save()  # Save customer
        return Response(  # Return success response
            {"message": "Customer registered successfully.", "id": customer.id},
            status=status.HTTP_201_CREATED,  # Return HTTP 201 status
        )


class EmployeeLoginAPIView(APIView):
    authentication_classes = []  # No authentication required
    permission_classes = []  # Allow all users

    def post(self, request):
        serializer = EmployeeLoginSerializer(data=request.data)  # Load request data
        serializer.is_valid(raise_exception=True)  # Validate login data
        employee = serializer.validated_data["employee"]  # Get validated employee

        tokens = _build_tokens(user_id=employee.id, role="employee")  # Generate JWT tokens
        return Response(tokens, status=status.HTTP_200_OK)  # Return tokens


class CustomerLoginAPIView(APIView):
    authentication_classes = []  # No authentication required
    permission_classes = []  # Allow all users

    def post(self, request):
        serializer = CustomerLoginSerializer(data=request.data)  # Load request data
        serializer.is_valid(raise_exception=True)  # Validate login data
        customer = serializer.validated_data["customer"]  # Get validated customer

        tokens = _build_tokens(user_id=customer.id, role="customer")  # Generate JWT tokens
        return Response(tokens, status=status.HTTP_200_OK)  # Return tokens
