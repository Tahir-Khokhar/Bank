from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from .models import Employee


class EmployeeRegisterView(View):
    template_name = 'employees/register.html'

    def get(self, request):
        return render(request, self.template_name)  # Render registration page

    def post(self, request):
        full_name = (request.POST.get('full_name') or '').strip()  # Strip to remove extra spaces
        username = (request.POST.get('username') or '').strip()  # Strip to remove extra spaces
        email = (request.POST.get('email') or '').strip()  # Strip to remove extra spaces
        password = request.POST.get('password') or ''  # Get password

        if not full_name:
            messages.error(request, 'Full name is required.')  # Display error message
        elif not username:
            messages.error(request, 'Username is required.')  # Display error message
        elif Employee.objects.filter(username=username).exists():  # Filter to search matching username
            messages.error(request, 'This username is already taken.')  # Display error message
        elif not email:
            messages.error(request, 'Email is required.')  # Display error message
        elif Employee.objects.filter(email=email).exists():  # Filter to search matching email
            messages.error(request, 'This email is already registered for an employee.')  # Display error message
        elif len(password) < 8:  # Check password length
            messages.error(request, 'Password must be at least 8 characters.')  # Display error message
        else:
            employee = Employee(full_name=full_name, username=username, email=email)
            employee.set_password(password)  # Hash password
            employee.save()  # Save employee
            messages.success(request, 'Employee account created. Please log in.')  # Display success message
            return redirect('/employees/login/')  # Redirect to login page

        return render(request, self.template_name)  # Render to reload registration page


class EmployeeLoginView(View):
    template_name = 'employees/login.html'

    def get(self, request):
        return render(request, self.template_name)  # Render login page

    def post(self, request):
        username = (request.POST.get('username') or '').strip()  # Strip to remove extra spaces
        password = request.POST.get('password') or ''  # Get password

        try:
            employee = Employee.objects.get(username=username, is_active=True)  # Get active employee
        except Employee.DoesNotExist:
            messages.error(request, 'Invalid username or password.')  # Display error message
            return render(request, self.template_name)  # Render to reload login page

        if not employee.check_password(password):  # Check password
            messages.error(request, 'Invalid username or password.')  # Display error message
            return render(request, self.template_name)  # Render to reload login page

        request.session['role'] = 'employee'  # Store role in session
        request.session['employee_id'] = employee.id  # Store employee ID in session
        messages.success(request, 'Login successful.')  # Display success message
        return redirect('/dashboard/employee/')  # Redirect to employee dashboard
