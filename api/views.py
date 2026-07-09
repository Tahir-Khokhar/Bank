from __future__ import annotations  # Postpone evaluation of type annotations until runtime

from rest_framework import status  # Provides HTTP status code constants (e.g., HTTP_200_OK)
from rest_framework.response import Response  # Creates HTTP responses for API views
from rest_framework.views import APIView  # Base class for building class-based API views

from .list_serializers import EmployeeListSerializer, CustomerListSerializer  # Import serializers for employee and customer lists


class EmployeeListAPIView(APIView):  # API endpoint for retrieving active employees
    authentication_classes = []  # No authentication is required
    permission_classes = []  # No permission checks; accessible to everyone

    def get(self, request):  # Handle HTTP GET requests
        qs = EmployeeListSerializer.Meta.model.objects.filter(is_active=True)  # Get all active employee records from the database
        serializer = EmployeeListSerializer(qs, many=True)  # Convert queryset into JSON-serializable data
        return Response(serializer.data, status=status.HTTP_200_OK)  # Return serialized data with HTTP 200 OK


class CustomerListAPIView(APIView):  # API endpoint for retrieving active customers
    authentication_classes = []  # No authentication is required
    permission_classes = []  # No permission checks; accessible to everyone

    def get(self, request):  # Handle HTTP GET requests
        qs = CustomerListSerializer.Meta.model.objects.filter(is_active=True)  # Get all active customer records from the database
        serializer = CustomerListSerializer(qs, many=True)  # Convert queryset into JSON-serializable data
        return Response(serializer.data, status=status.HTTP_200_OK)  # Return serialized data with HTTP 200 OK
