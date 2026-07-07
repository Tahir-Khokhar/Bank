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


def _build_tokens(*, user_id: int, role: str) -> dict:
    """Create refresh/access tokens with role + user_id claims."""
    refresh = RefreshToken()
    refresh["role"] = role
    refresh["user_id"] = user_id

    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class EmployeeRegisterAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = EmployeeRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        return Response(
            {"message": "Employee registered successfully.", "id": employee.id},
            status=status.HTTP_201_CREATED,
        )


class CustomerRegisterAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        return Response(
            {"message": "Customer registered successfully.", "id": customer.id},
            status=status.HTTP_201_CREATED,
        )


class EmployeeLoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = EmployeeLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.validated_data["employee"]

        tokens = _build_tokens(user_id=employee.id, role="employee")
        return Response(tokens, status=status.HTTP_200_OK)


class CustomerLoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = CustomerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.validated_data["customer"]

        tokens = _build_tokens(user_id=customer.id, role="customer")
        return Response(tokens, status=status.HTTP_200_OK)


