# Enable postponed evaluation of type hints
from __future__ import annotations

# Import Django messages framework to display success and error messages
from django.contrib import messages

# Import redirect function to redirect users to another page
from django.shortcuts import redirect

# Import the Customer model
from customers.models import Customer

# Import the Employee model
from employees.models import Employee


# -------------------- Lookup Helper Functions --------------------


# Return the currently logged-in customer
def get_current_customer(request):
    """Return the logged-in Customer, or ``None``."""

    # Check if the logged-in user is a customer
    if request.session.get("role") != "customer":
        return None

    # Get the customer ID from the session
    customer_id = request.session.get("customer_id")

    # Return None if no customer ID exists
    if not customer_id:
        return None

    # Get the active customer and load its related branch in one query
    return (
        Customer.objects.filter(pk=customer_id, is_active=True)
        .select_related("branch")
        .first()
    )


# Return the currently logged-in employee
def get_current_employee(request):
    """Return the logged-in Employee (manager or staff), or ``None``."""

    # Check if the logged-in user is an employee or manager
    if request.session.get("role") not in {"employee", "manager"}:
        return None

    # Get the employee ID from the session
    employee_id = request.session.get("employee_id")

    # Return None if no employee ID exists
    if not employee_id:
        return None

    # Get the active employee and load its related branch in one query
    return (
        Employee.objects.filter(pk=employee_id, is_active=True)
        .select_related("branch")
        .first()
    )


# Return the currently logged-in user and their role
def get_current_actor(request):
    """Return a tuple ``(role, instance)`` for whoever is logged in."""

    # Try to get the logged-in customer
    customer = get_current_customer(request)

    # Return customer information if found
    if customer:
        return "customer", customer

    # Try to get the logged-in employee
    employee = get_current_employee(request)

    # Return manager or employee based on role
    if employee:
        return ("manager" if employee.is_manager else "employee"), employee

    # Return None if no user is logged in
    return None, None


# Return the client's IP address
def client_ip(request):

    # Get forwarded IP address if the app is behind a proxy
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

    # Return the first IP address from the forwarded list
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Otherwise return the direct client IP address
    return request.META.get("REMOTE_ADDR")


# -------------------- Access Control Mixins --------------------


# Allow access only to logged-in customers
class CustomerRequiredMixin:
    """Allow only logged-in customers; attach ``self.customer``."""

    # Login page URL
    login_url = "/customers/login/"

    # Run before every request
    def dispatch(self, request, *args, **kwargs):

        # Get the logged-in customer
        customer = get_current_customer(request)

        # Redirect to login if not authenticated
        if not customer:
            messages.error(request, "Please log in to continue.")
            return redirect(self.login_url)

        # Save customer object for later use
        self.customer = customer

        # Attach customer to the request object
        request.current_customer = customer

        # Continue processing the request
        return super().dispatch(request, *args, **kwargs)


# Allow access only to employees and managers
class EmployeeRequiredMixin:
    """Allow logged-in employees and managers; attach ``self.employee``."""

    # Login page URL
    login_url = "/employees/login/"

    # Run before every request
    def dispatch(self, request, *args, **kwargs):

        # Get the logged-in employee
        employee = get_current_employee(request)

        # Redirect if the user is not logged in
        if not employee:
            messages.error(request, "Please log in to continue.")
            return redirect(self.login_url)

        # Prevent suspended employees from accessing the system
        if employee.is_suspended:
            messages.error(request, "Your account is suspended. Contact the branch manager.")

            # Clear the current session
            request.session.flush()

            # Redirect to login page
            return redirect(self.login_url)

        # Save employee object for later use
        self.employee = employee

        # Attach employee to the request object
        request.current_employee = employee

        # Continue processing the request
        return super().dispatch(request, *args, **kwargs)


# Allow access only to managers
class ManagerRequiredMixin:
    """Allow only branch managers (admin dashboard); attach ``self.employee``."""

    # Login page URL
    login_url = "/employees/login/"

    # Run before every request
    def dispatch(self, request, *args, **kwargs):

        # Get the logged-in employee
        employee = get_current_employee(request)

        # Redirect if not logged in
        if not employee:
            messages.error(request, "Please log in to continue.")
            return redirect(self.login_url)

        # Prevent suspended employees from accessing the system
        if employee.is_suspended:
            messages.error(request, "Your account is suspended. Contact the branch manager.")
            request.session.flush()
            return redirect(self.login_url)

        # Allow only managers
        if not employee.is_manager:
            messages.error(request, "This area is restricted to branch managers.")
            return redirect("/dashboard/employee/")

        # Save employee object
        self.employee = employee

        # Attach employee to the request
        request.current_employee = employee

        # Continue processing the request
        return super().dispatch(request, *args, **kwargs)


# Allow access to any authenticated user
class LoginRequiredAnyMixin:
    """Allow any authenticated actor (customer, employee, manager)."""

    # Run before every request
    def dispatch(self, request, *args, **kwargs):

        # Get the current user's role and object
        role, actor = get_current_actor(request)

        # Redirect if no user is logged in
        if not actor:
            messages.error(request, "Please log in to continue.")
            return redirect("/")

        # Save user role
        self.role = role

        # Save user object
        self.actor = actor

        # Check whether the user is staff
        self.is_staff = role in {"employee", "manager"}

        # Check whether the user is a manager
        self.is_manager = role == "manager"

        # Set the correct dashboard URL
        self.dashboard_home_url = {
            "customer": "/dashboard/customer/",
            "employee": "/dashboard/employee/",
            "manager": "/dashboard/admin/",
        }.get(role, "/")

        # Continue processing the request
        return super().dispatch(request, *args, **kwargs)


# Allow access only to employees and managers
class StaffRequiredMixin(LoginRequiredAnyMixin):
    """Allow only employees and managers (not customers)."""

    # Run before every request
    def dispatch(self, request, *args, **kwargs):

        # Get the current user's role
        role, actor = get_current_actor(request)

        # Block customers and unauthenticated users
        if not actor or role not in {"employee", "manager"}:
            messages.error(request, "This area is restricted to bank staff.")
            return redirect("/")

        # Continue processing the request
        return super().dispatch(request, *args, **kwargs)
