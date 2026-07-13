
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from accounts.models import Account
from dashboard.auth import (
    CustomerRequiredMixin,
    LoginRequiredAnyMixin,
    client_ip,
)
from dashboard.models import ActivityLog
from dashboard.services import (
    BankingError,
    deposit,
    log_activity,
    notify_all_managers,
    notify_customer,
    withdraw,
)
from loans.models import Loan, LoanRepayment
from transactions.models import Transaction

# Default annual interest rate per loan type (%).
DEFAULT_RATES = {
    Loan.LoanType.PERSONAL: Decimal("18.00"),
    Loan.LoanType.HOME: Decimal("11.00"),
    Loan.LoanType.CAR: Decimal("14.00"),
    Loan.LoanType.BUSINESS: Decimal("16.00"),
    Loan.LoanType.EDUCATION: Decimal("9.00"),
}


def _dec(raw):
    try:
        return Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError):
        return None


class LoanListView(LoginRequiredAnyMixin, TemplateView):
    template_name = "loans/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = Loan.objects.select_related("customer", "account")
        if self.role == "customer":
            qs = qs.filter(customer=self.actor)

        status = self.request.GET.get("status") or ""
        search = (self.request.GET.get("q") or "").strip()
        if status:
            qs = qs.filter(status=status)
        if search and self.is_staff:
            from django.db.models import Q
            qs = qs.filter(Q(reference__icontains=search) |
                           Q(customer__full_name__icontains=search))

        paginator = Paginator(qs, 12)
        page = paginator.get_page(self.request.GET.get("page"))
        ctx.update({
            "page_title": "Loans",
            "active_nav": "loans",
            "dashboard_home_url": self.dashboard_home_url,
            "current_role": self.role,
            "page_obj": page,
            "loans": page.object_list,
            "status": status,
            "search": search,
            "statuses": Loan.Status.choices,
            "querystring": f"status={status}&q={search}",
            "is_staff": self.is_staff,
        })
        return ctx


class LoanDetailView(LoginRequiredAnyMixin, TemplateView):
    template_name = "loans/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = Loan.objects.select_related("customer", "account", "approved_by", "reviewed_by")
        if self.role == "customer":
            qs = qs.filter(customer=self.actor)
        loan = get_object_or_404(qs, pk=kwargs["pk"])
        can_decide = self.role == "manager" or (
            self.role == "employee" and getattr(self.actor, "can_approve_loans", False))
        ctx.update({
            "page_title": f"Loan {loan.reference}",
            "active_nav": "loans",
            "dashboard_home_url": self.dashboard_home_url,
            "current_role": self.role,
            "loan": loan,
            "repayments": loan.repayments.all(),
            "is_staff": self.is_staff,
            "can_decide": can_decide,
            "customer_accounts": list(loan.customer.accounts.exclude(
                status=Account.Status.CLOSED)) if self.is_staff else [],
        })
        return ctx


class LoanApplyView(CustomerRequiredMixin, View):
    template_name = "loans/apply.html"

    def _context(self, **extra):
        base = {
            "page_title": "Apply for a Loan",
            "active_nav": "loans",
            "dashboard_home_url": "/dashboard/customer/",
            "current_role": "customer",
            "loan_types": Loan.LoanType.choices,
            "accounts": self.customer.accounts.exclude(status=Account.Status.CLOSED),
            "default_rates": {k: str(v) for k, v in DEFAULT_RATES.items()},
        }
        base.update(extra)
        return base

    def get(self, request):
        return render(request, self.template_name, self._context())

    def post(self, request):
        data = request.POST
        loan_type = data.get("loan_type") or Loan.LoanType.PERSONAL
        principal = _dec(data.get("principal_amount"))
        tenure = data.get("tenure_months")
        purpose = (data.get("purpose") or "").strip()

        if principal is None or principal <= 0:
            messages.error(request, "Enter a valid loan amount.")
            return render(request, self.template_name, self._context())
        try:
            tenure = int(tenure)
        except (TypeError, ValueError):
            tenure = 0
        if tenure <= 0:
            messages.error(request, "Enter a valid tenure in months.")
            return render(request, self.template_name, self._context())

        account = None
        if data.get("account"):
            account = Account.objects.filter(pk=data.get("account"),
                                             customer=self.customer).first()

        loan = Loan(
            customer=self.customer, account=account, loan_type=loan_type,
            principal_amount=principal, tenure_months=tenure,
            interest_rate=DEFAULT_RATES.get(loan_type, Decimal("12.00")),
            purpose=purpose, status=Loan.Status.PENDING,
        )
        loan.save()
        notify_all_managers("New loan application",
                            f"{self.customer.full_name} applied for a {loan.get_loan_type_display()} of Rs {principal}.",
                            category="loan", url=f"/loans/{loan.id}/")
        log_activity(action=f"Applied for {loan.get_loan_type_display()} (Rs {principal})",
                     category=ActivityLog.Category.LOAN, customer=self.customer,
                     ip_address=client_ip(request))
        messages.success(request, f"Loan application submitted. Ref: {loan.reference}")
        return redirect("loan-detail", pk=loan.pk)


class LoanDecisionView(LoginRequiredAnyMixin, View):
    """Staff action: review / approve / reject / disburse a loan."""

    def post(self, request, pk):
        can_decide = self.role == "manager" or (
            self.role == "employee" and getattr(self.actor, "can_approve_loans", False))
        action = request.POST.get("action")
        loan = get_object_or_404(Loan, pk=pk)

        # "Forward to manager" is allowed for any staff member.
        if action == "review":
            if not self.is_staff:
                messages.error(request, "Not permitted.")
                return redirect("loan-detail", pk=pk)
            loan.status = Loan.Status.UNDER_REVIEW
            loan.reviewed_by = self.actor
            loan.save(update_fields=["status", "reviewed_by", "updated_at"])
            notify_all_managers("Loan forwarded for review",
                                f"Loan {loan.reference} needs manager review.",
                                category="loan", url=f"/loans/{loan.id}/")
            messages.success(request, "Loan forwarded to manager for review.")
            return redirect("loan-detail", pk=pk)

        if not can_decide:
            messages.error(request, "You do not have permission to decide on loans.")
            return redirect("loan-detail", pk=pk)

        note = (request.POST.get("note") or "").strip()

        if action == "approve":
            loan.status = Loan.Status.APPROVED
            loan.approved_by = self.actor
            loan.decided_at = timezone.now()
            loan.decision_note = note
            loan.save()
            notify_customer(loan.customer, "Loan approved",
                            f"Your loan {loan.reference} has been approved.",
                            category="loan", url=f"/loans/{loan.id}/")
            log_activity(action=f"Approved loan {loan.reference}",
                         category=ActivityLog.Category.LOAN, employee=self.actor,
                         customer=loan.customer, ip_address=client_ip(request))
            messages.success(request, "Loan approved.")

        elif action == "reject":
            loan.status = Loan.Status.REJECTED
            loan.approved_by = self.actor
            loan.decided_at = timezone.now()
            loan.decision_note = note
            loan.save()
            notify_customer(loan.customer, "Loan rejected",
                            f"Your loan {loan.reference} was rejected. {note}",
                            category="loan", url=f"/loans/{loan.id}/")
            log_activity(action=f"Rejected loan {loan.reference}",
                         category=ActivityLog.Category.LOAN, employee=self.actor,
                         customer=loan.customer, ip_address=client_ip(request))
            messages.success(request, "Loan rejected.")

        elif action == "disburse":
            if loan.status != Loan.Status.APPROVED:
                messages.error(request, "Only approved loans can be disbursed.")
                return redirect("loan-detail", pk=pk)
            account = loan.account or loan.customer.primary_account
            if not account:
                account_id = request.POST.get("account")
                account = Account.objects.filter(pk=account_id, customer=loan.customer).first()
            if not account:
                messages.error(request, "Select a disbursement account.")
                return redirect("loan-detail", pk=pk)
            try:
                # Credit the loan amount into the customer's account.
                deposit(account, loan.principal_amount, employee=self.actor,
                        channel=Transaction.Channel.SYSTEM,
                        description=f"Loan disbursement {loan.reference}")
            except BankingError as exc:
                messages.error(request, str(exc))
                return redirect("loan-detail", pk=pk)
            loan.account = account
            loan.status = Loan.Status.ACTIVE
            loan.disbursed_at = timezone.now()
            loan.save()
            notify_customer(loan.customer, "Loan disbursed",
                            f"Rs {loan.principal_amount} credited to {account.account_number}.",
                            category="loan", url=f"/loans/{loan.id}/")
            log_activity(action=f"Disbursed loan {loan.reference}",
                         category=ActivityLog.Category.LOAN, employee=self.actor,
                         customer=loan.customer, ip_address=client_ip(request))
            messages.success(request, "Loan disbursed to customer account.")
        else:
            messages.error(request, "Unknown action.")
        return redirect("loan-detail", pk=pk)


class LoanRepaymentView(LoginRequiredAnyMixin, View):
    """Record a repayment. Customers pay from their own account; staff may
    record any repayment."""

    def post(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        if self.role == "customer" and loan.customer_id != self.actor.id:
            messages.error(request, "Not permitted.")
            return redirect("loan-list")
        if loan.status not in (Loan.Status.ACTIVE, Loan.Status.DISBURSED):
            messages.error(request, "This loan is not active.")
            return redirect("loan-detail", pk=pk)

        amount = _dec(request.POST.get("amount"))
        if amount is None or amount <= 0:
            messages.error(request, "Enter a valid amount.")
            return redirect("loan-detail", pk=pk)
        # Never collect more than what is still owed on the loan.
        amount = min(amount, loan.remaining_amount)

        method = request.POST.get("method") or LoanRepayment.Method.ACCOUNT
        emp = self.actor if self.is_staff else None

        # If paying via account debit, withdraw funds first.
        if method == LoanRepayment.Method.ACCOUNT:
            account = loan.account or loan.customer.primary_account
            if self.role == "customer" and request.POST.get("account"):
                account = Account.objects.filter(pk=request.POST.get("account"),
                                                 customer=self.actor).first()
            if not account:
                messages.error(request, "No account available for debit.")
                return redirect("loan-detail", pk=pk)
            try:
                withdraw(account, amount, employee=emp,
                         channel=Transaction.Channel.SYSTEM,
                         description=f"Loan repayment {loan.reference}")
            except BankingError as exc:
                messages.error(request, str(exc))
                return redirect("loan-detail", pk=pk)

        LoanRepayment.objects.create(loan=loan, amount=amount, method=method,
                                     recorded_by=emp)
        loan.amount_paid = (loan.amount_paid or Decimal("0")) + amount
        if loan.remaining_amount <= 0:
            loan.status = Loan.Status.CLOSED
        loan.save(update_fields=["amount_paid", "status", "updated_at"])
        notify_customer(loan.customer, "Loan repayment received",
                        f"Rs {amount} received for loan {loan.reference}.",
                        category="loan", url=f"/loans/{loan.id}/")
        log_activity(action=f"Repayment Rs {amount} for loan {loan.reference}",
                     category=ActivityLog.Category.LOAN, employee=emp,
                     customer=loan.customer if not self.is_staff else None,
                     actor_name=self.actor.full_name, actor_role=self.role,
                     ip_address=client_ip(request))
        messages.success(request, "Repayment recorded.")
        return redirect("loan-detail", pk=pk)
