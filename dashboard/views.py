# Enable postponed evaluation of type hints
from __future__ import annotations

# Import JSON module
import json

# Import Decimal for precise money calculations
from decimal import Decimal

# Import Django message framework
from django.contrib import messages

# Import paginator for pagination
from django.core.paginator import Paginator

# Import redirect helper
from django.shortcuts import redirect

# Import generic class-based views
from django.views.generic import TemplateView, View

# Import Account model
from accounts.models import Account

# Import Customer model
from customers.models import Customer

# Import analytics helper functions
from dashboard import analytics

# Import authentication helpers and mixins
from dashboard.auth import (
    CustomerRequiredMixin,
    EmployeeRequiredMixin,
    ManagerRequiredMixin,
    get_current_actor,
)

# Import dashboard models
from dashboard.models import ActivityLog, Notification

# Import Employee model
from employees.models import Employee

# Import Loan model
from loans.models import Loan

# Import Transaction model
from transactions.models import Transaction


# Display the customer dashboard
class CustomerDashboardView(CustomerRequiredMixin, TemplateView):

    # Template used for this page
    template_name = "dashboard/customer.html"

    # Build template context
    def get_context_data(self, **kwargs):

        # Get default context
        ctx = super().get_context_data(**kwargs)

        # Get logged-in customer
        customer = self.customer

        # Get all customer accounts
        accounts = list(
            customer.accounts.select_related("branch").all()
        )

        # Get primary account
        primary = customer.primary_account

        # Create a list of account IDs
        account_ids = [a.id for a in accounts]

        # Get all customer transactions
        txns = (
            Transaction.objects.filter(account_id__in=account_ids)
            .select_related("account")
            .order_by("-created_at")
        )

        # Get latest 8 transactions
        recent = list(txns[:8])

        # Calculate total incoming money
        incoming = analytics.money(
            analytics._sum(
                txns.filter(
                    direction=Transaction.Direction.CREDIT,
                    status=Transaction.Status.SUCCESS,
                )
            )
        )

        # Calculate total outgoing money
        outgoing = analytics.money(
            analytics._sum(
                txns.filter(
                    direction=Transaction.Direction.DEBIT,
                    status=Transaction.Status.SUCCESS,
                )
            )
        )

        # Get customer loans
        loans = list(customer.loans.all())

        # Get active loans only
        active_loans = [l for l in loans if l.is_open]

        # Prepare transaction chart data
        chart = (
            analytics.monthly_transaction_series(6, account=primary)
            if primary
            else {"labels": [], "credit": [], "debit": []}
        )

        # Add values to template context
        ctx.update({
            "page_title": "My Dashboard",
            "active_nav": "home",
            "dashboard_home_url": "/dashboard/customer/",
            "customer": customer,
            "accounts": accounts,
            "primary_account": primary,
            "total_balance": sum((a.balance for a in accounts), Decimal("0.00")),
            "available_balance": sum((a.available_balance for a in accounts), Decimal("0.00")),
            "recent_transactions": recent,
            "incoming_total": incoming,
            "outgoing_total": outgoing,
            "transaction_count": txns.count(),
            "loans": loans,
            "active_loan_count": len(active_loans),
            "pending_loan_count": len([
                l for l in loans
                if l.status in (
                    Loan.Status.PENDING,
                    Loan.Status.UNDER_REVIEW,
                )
            ]),
            "chart_data": json.dumps(chart),
        })

        # Return context
        return ctx


# Display employee dashboard
class EmployeeDashboardView(EmployeeRequiredMixin, TemplateView):

    # Template used for this page
    template_name = "dashboard/employee.html"

    # Build template context
    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        # Get dashboard statistics
        stats = analytics.employee_stats()

        # Get pending loans
        pending_loans = list(
            Loan.objects.filter(
                status__in=[
                    Loan.Status.PENDING,
                    Loan.Status.UNDER_REVIEW,
                ]
            ).select_related("customer")[:6]
        )

        # Get recently added customers
        recent_customers = list(
            Customer.objects.select_related("branch")
            .order_by("-created_at")[:6]
        )

        # Get latest transactions
        recent_txns = list(
            Transaction.objects.select_related(
                "account",
                "account__customer",
            ).order_by("-created_at")[:8]
        )

        # Add values to context
        ctx.update({
            "page_title": "Employee Dashboard",
            "active_nav": "home",
            "dashboard_home_url": "/dashboard/employee/",
            "stats": stats,
            "pending_loans": pending_loans,
            "recent_customers": recent_customers,
            "recent_transactions": recent_txns,
            "daily_chart": json.dumps(
                analytics.daily_transaction_series(7)
            ),
            "loan_chart": json.dumps(
                analytics.loan_status_breakdown()
            ),
        })

        return ctx


# Display manager dashboard
class AdminDashboardView(ManagerRequiredMixin, TemplateView):

    # Template used for this page
    template_name = "dashboard/admin.html"

    # Build template context
    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        # Get overall bank statistics
        stats = analytics.bank_wide_stats()

        # Get recent activity logs
        recent_activity = list(ActivityLog.objects.all()[:10])

        # Get pending loans
        pending_loans = list(
            Loan.objects.filter(
                status__in=[
                    Loan.Status.PENDING,
                    Loan.Status.UNDER_REVIEW,
                ]
            ).select_related("customer")[:6]
        )

        # Get latest transactions
        recent_txns = list(
            Transaction.objects.select_related(
                "account",
                "account__customer",
            ).order_by("-created_at")[:8]
        )

        # Build approval chart data
        approval_chart = {
            "labels": ["Approved", "Pending", "Rejected"],
            "data": [
                stats["approved_loans"] + stats["active_loans"],
                stats["pending_loans"],
                stats["rejected_loans"],
            ],
        }

        # Add values to context
        ctx.update({
            "page_title": "Branch Manager Dashboard",
            "active_nav": "home",
            "dashboard_home_url": "/dashboard/admin/",
            "stats": stats,
            "recent_activity": recent_activity,
            "pending_loans": pending_loans,
            "recent_transactions": recent_txns,
            "monthly_chart": json.dumps(
                analytics.monthly_transaction_series(6)
            ),
            "customer_growth": json.dumps(
                analytics.monthly_count_series(
                    Customer.objects.all(),
                    "created_at",
                    6,
                )
            ),
            "loan_chart": json.dumps(
                analytics.loan_status_breakdown()
            ),
            "approval_chart": json.dumps(approval_chart),
        })

        return ctx


# Display user notifications
class NotificationListView(TemplateView):

    # Template used for this page
    template_name = "dashboard/notifications.html"

    # Check user before processing request
    def dispatch(self, request, *args, **kwargs):

        # Get current logged-in user
        role, actor = get_current_actor(request)

        # Redirect if not logged in
        if not actor:
            messages.error(request, "Please log in to continue.")
            return redirect("/")

        self.role = role
        self.actor = actor

        return super().dispatch(request, *args, **kwargs)

    # Get notifications for current user
    def get_queryset(self):

        if self.role == "customer":
            return Notification.objects.filter(
                audience=Notification.Audience.CUSTOMER,
                customer=self.actor,
            )

        return Notification.objects.filter(
            audience=Notification.Audience.EMPLOYEE,
            employee=self.actor,
        )

    # Handle GET request
    def get(self, request, *args, **kwargs):

        # Mark unread notifications as read
        self.get_queryset().filter(
            is_read=False
        ).update(is_read=True)

        return super().get(request, *args, **kwargs)

    # Build template context
    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        # Create paginator
        paginator = Paginator(self.get_queryset(), 15)

        # Get requested page
        page = paginator.get_page(
            self.request.GET.get("page")
        )

        # Dashboard home link
        home = {
            "customer": "/dashboard/customer/",
            "employee": "/dashboard/employee/",
            "manager": "/dashboard/admin/",
        }.get(self.role, "/")

        ctx.update({
            "page_title": "Notifications",
            "active_nav": "notifications",
            "dashboard_home_url": home,
            "page_obj": page,
            "notifications": page.object_list,
        })

        return ctx


# Mark all notifications as read
class MarkNotificationsReadView(View):

    # Handle POST request
    def post(self, request):

        # Get current user
        role, actor = get_current_actor(request)

        # Redirect if not logged in
        if not actor:
            return redirect("/")

        # Update customer notifications
        if role == "customer":
            Notification.objects.filter(
                customer=actor,
                is_read=False,
            ).update(is_read=True)

        # Update employee notifications
        else:
            Notification.objects.filter(
                employee=actor,
                is_read=False,
            ).update(is_read=True)

        # Show success message
        messages.success(
            request,
            "All notifications marked as read."
        )

        return redirect("/dashboard/notifications/")


# Display activity logs
class ActivityLogView(ManagerRequiredMixin, TemplateView):

    # Template used for this page
    template_name = "dashboard/activity.html"

    # Build template context
    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        # Get all activity logs
        logs = ActivityLog.objects.all()

        # Get selected category
        category = self.request.GET.get("category")

        # Filter logs by category
        if category:
            logs = logs.filter(category=category)

        # Create paginator
        paginator = Paginator(logs, 25)

        # Get requested page
        page = paginator.get_page(
            self.request.GET.get("page")
        )

        # Add values to context
        ctx.update({
            "page_title": "Activity & Audit Logs",
            "active_nav": "activity",
            "dashboard_home_url": "/dashboard/admin/",
            "page_obj": page,
            "logs": page.object_list,
            "categories": ActivityLog.Category.choices,
            "selected_category": category or "",
        })

        return ctx
