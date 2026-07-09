"""Dashboard views (class-based only)."""

from __future__ import annotations

from django.views.generic import TemplateView


class AdminDashboardView(TemplateView):
    # Render the Admin dashboard page.

    template_name = 'dashboard/admin.html'


class EmployeeDashboardView(TemplateView):
    # Render the Employee dashboard page.

    template_name = 'dashboard/employee.html'


class CustomerDashboardView(TemplateView):
    # Render the Customer dashboard page.

    template_name = 'dashboard/customer.html'

