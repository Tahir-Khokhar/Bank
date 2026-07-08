from __future__ import annotations
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View
from .models import Customer


class CustomerRegisterView(View):
    template_name = 'customers/register.html'

    def get(self, request):
        return render(request, self.template_name)  # Render registration page

    def post(self, request):
        full_name = (request.POST.get('full_name') or '').strip()  # Get and clean full name
        username = (request.POST.get('username') or '').strip()  # Get and clean username
        email = (request.POST.get('email') or '').strip()  # Get and clean email
        password = request.POST.get('password') or ''  # Get password

        if not full_name:
            messages.error(request, 'Full name is required.')  # Show error message
        elif not username:
            messages.error(request, 'Username is required.')  # Show error message
        elif Customer.objects.filter(username=username).exists():  # Check username exists
            messages.error(request, 'This username is already taken.')  # Show error message
        elif not email:
            messages.error(request, 'Email is required.')  # Show error message
        elif Customer.objects.filter(email=email).exists():  # Check email exists
            messages.error(request, 'This email is already registered for a customer.')  # Show error message
        elif len(password) < 8:  # Check password length
            messages.error(request, 'Password must be at least 8 characters.')  # Show error message
        else:
            customer = Customer(full_name=full_name, username=username, email=email)
            customer.set_password(password)  # Hash password
            customer.save()  # Save customer
            messages.success(request, 'Customer account created. Please log in.')  # Show success message
            return redirect('/customers/login/')  # Redirect to login page

        return render(request, self.template_name)  # Reload registration page


class CustomerLoginView(View):
    template_name = 'customers/login.html'

    def get(self, request):
        return render(request, self.template_name)  # Render login page

    def post(self, request):
        username = (request.POST.get('username') or '').strip()  # Get and clean username
        password = request.POST.get('password') or ''  # Get password

        try:
            customer = Customer.objects.get(username=username, is_active=True)  # Get active customer
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid username or password.')  # Show error message
            return render(request, self.template_name)  # Reload login page

        if not customer.check_password(password):  # Verify password
            messages.error(request, 'Invalid username or password.')  # Show error message
            return render(request, self.template_name)  # Reload login page

        request.session['role'] = 'customer'  # Store role in session
        request.session['customer_id'] = customer.id  # Store customer ID in session
        messages.success(request, 'Login successful.')  # Show success message
        return redirect('/dashboard/customer/')  # Redirect to dashboard
