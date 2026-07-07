from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from .models import Customer


class CustomerRegisterView(View):
    template_name = 'customers/register.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        full_name = (request.POST.get('full_name') or '').strip()
        username = (request.POST.get('username') or '').strip()
        email = (request.POST.get('email') or '').strip()
        password = request.POST.get('password') or ''

        if not full_name:
            messages.error(request, 'Full name is required.')
        elif not username:
            messages.error(request, 'Username is required.')
        elif Customer.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken.')
        elif not email:
            messages.error(request, 'Email is required.')
        elif Customer.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered for a customer.')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            customer = Customer(full_name=full_name, username=username, email=email)
            customer.set_password(password)
            customer.save()
            messages.success(request, 'Customer account created. Please log in.')
            return redirect('/customers/login/')

        return render(request, self.template_name)


class CustomerLoginView(View):
    template_name = 'customers/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''

        try:
            customer = Customer.objects.get(username=username, is_active=True)
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid username or password.')
            return render(request, self.template_name)

        if not customer.check_password(password):
            messages.error(request, 'Invalid username or password.')
            return render(request, self.template_name)

        request.session['role'] = 'customer'
        request.session['customer_id'] = customer.id
        messages.success(request, 'Login successful.')
        return redirect('/dashboard/customer/')

