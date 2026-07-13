

from __future__ import annotations

from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import Account
from customers.models import Customer
from dashboard.auth import LoginRequiredAnyMixin, StaffRequiredMixin
from dashboard.exports import export_dispatch
from loans.models import Loan
from transactions.models import Transaction


class ReportsHomeView(LoginRequiredAnyMixin, TemplateView):
    template_name = "reports/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        accounts = []
        if self.role == "customer":
            accounts = list(self.actor.accounts.select_related("branch").all())
        ctx.update({
            "page_title": "Reports & Statements",
            "active_nav": "reports",
            "dashboard_home_url": self.dashboard_home_url,
            "current_role": self.role,
            "is_staff": self.is_staff,
            "accounts": accounts,
        })
        return ctx


class StatementReportView(LoginRequiredAnyMixin, TemplateView):
    template_name = "reports/statement.html"

    def _resolve_account(self):
        if self.role == "customer":
            acc_id = self.request.GET.get("account")
            qs = self.actor.accounts.select_related("branch", "customer")
            if acc_id:
                return qs.filter(pk=acc_id).first()
            return qs.first()
        # staff: by account number
        number = (self.request.GET.get("account_number") or "").strip()
        if number:
            return Account.objects.select_related("branch", "customer").filter(
                account_number=number).first()
        return None

    def _date_range(self, period):
        today = timezone.now().date()
        if period == "month":
            return today.replace(day=1), today
        if period == "year":
            return today.replace(month=1, day=1), today
        if period == "custom":
            return (self.request.GET.get("from") or None,
                    self.request.GET.get("to") or None)
        return None, None  # mini / all

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Build the statement from the chosen account and date range.
        account = self._resolve_account()
        period = self.request.GET.get("period", "month")

        rows = []
        summary = {"opening": Decimal("0.00"), "closing": Decimal("0.00"),
                   "credits": Decimal("0.00"), "debits": Decimal("0.00"), "count": 0}
        txns = []
        if account:
            qs = account.transactions.order_by("created_at")
            start, end = self._date_range(period)
            if start:
                qs = qs.filter(created_at__date__gte=start)
            if end:
                qs = qs.filter(created_at__date__lte=end)
            if period == "mini":
                txns = list(account.transactions.order_by("-created_at")[:10])
                txns.reverse()
            else:
                txns = list(qs)

            # Add up credits/debits and work out the opening/closing balances.
            for t in txns:
                if t.direction == Transaction.Direction.CREDIT:
                    summary["credits"] += t.amount
                else:
                    summary["debits"] += t.amount
            summary["count"] = len(txns)
            summary["closing"] = account.balance
            if txns:
                first = txns[0]
                delta = summary["credits"] - summary["debits"]
                summary["opening"] = first.balance_after - (
                    first.amount if first.direction == Transaction.Direction.CREDIT
                    else -first.amount)

        ctx.update({
            "page_title": "Account Statement",
            "active_nav": "reports",
            "dashboard_home_url": self.dashboard_home_url,
            "current_role": self.role,
            "is_staff": self.is_staff,
            "account": account,
            "transactions": txns,
            "summary": summary,
            "period": period,
            "date_from": self.request.GET.get("from", ""),
            "date_to": self.request.GET.get("to", ""),
            "accounts": list(self.actor.accounts.all()) if self.role == "customer" else [],
        })

        fmt = self.request.GET.get("export")
        if fmt and account:
            # Stash the data so render_to_response can export it.
            ctx["_export"] = (fmt, account, txns, summary, period)
        return ctx

    def render_to_response(self, context, **kwargs):
        exp = context.get("_export")
        if exp:
            fmt, account, txns, summary, period = exp
            header = ["Date", "Reference", "Type", "Description", "Debit", "Credit", "Balance"]
            rows = [header]
            for t in txns:
                debit = t.amount if t.direction == Transaction.Direction.DEBIT else ""
                credit = t.amount if t.direction == Transaction.Direction.CREDIT else ""
                rows.append([
                    t.created_at.strftime("%Y-%m-%d"), t.reference,
                    t.get_txn_type_display(), t.description,
                    f"{debit}" if debit != "" else "", f"{credit}" if credit != "" else "",
                    f"{t.balance_after}",
                ])
            subtitle = (f"Account {account.account_number} • {account.customer.full_name} "
                        f"• Period: {period}")
            # Send the statement rows to the shared Excel/PDF writer.
            return export_dispatch(fmt, rows, f"statement_{account.account_number}",
                                   title="Account Statement", subtitle=subtitle)
        return super().render_to_response(context, **kwargs)


class TransactionReportView(StaffRequiredMixin, TemplateView):
    template_name = "reports/transaction_report.html"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = Transaction.objects.select_related("account", "account__customer")
        period = self.request.GET.get("period", "month")
        today = timezone.now().date()
        if period == "today":
            qs = qs.filter(created_at__date=today)
        elif period == "week":
            qs = qs.filter(created_at__date__gte=today - timezone.timedelta(days=7))
        elif period == "month":
            qs = qs.filter(created_at__date__gte=today.replace(day=1))
        elif period == "year":
            qs = qs.filter(created_at__date__gte=today.replace(month=1, day=1))

        txns = list(qs.order_by("-created_at")[:2000])
        credits = sum((t.amount for t in txns if t.direction == "credit"), Decimal("0"))
        debits = sum((t.amount for t in txns if t.direction == "debit"), Decimal("0"))
        ctx.update({
            "page_title": "Transaction Report",
            "active_nav": "reports",
            "dashboard_home_url": self.dashboard_home_url,
            "current_role": self.role,
            "is_staff": self.is_staff,
            "transactions": txns[:200],
            "count": len(txns),
            "credits": credits,
            "debits": debits,
            "period": period,
        })
        fmt = self.request.GET.get("export")
        if fmt:
            ctx["_export_rows"] = txns
        return ctx

    def render_to_response(self, context, **kwargs):
        if context.get("_export_rows") is not None:
            fmt = self.request.GET.get("export")
            header = ["Reference", "Date", "Account", "Customer", "Type", "Direction",
                      "Amount", "Status"]
            rows = [header]
            for t in context["_export_rows"]:
                rows.append([t.reference, t.created_at.strftime("%Y-%m-%d %H:%M"),
                             t.account.account_number, t.account.customer.full_name,
                             t.get_txn_type_display(), t.get_direction_display(),
                             f"{t.amount}", t.get_status_display()])
            return export_dispatch(fmt, rows, "transaction_report",
                                   title="Transaction Report")
        return super().render_to_response(context, **kwargs)


class CustomerReportView(StaffRequiredMixin, TemplateView):
    template_name = "reports/customer_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Load every customer with their branch and accounts for the report.
        customers = list(Customer.objects.select_related("branch")
                         .prefetch_related("accounts").order_by("-created_at"))
        ctx.update({
            "page_title": "Customer Report",
            "active_nav": "reports",
            "dashboard_home_url": self.dashboard_home_url,
            "current_role": self.role,
            "is_staff": self.is_staff,
            "customers": customers[:300],
            "count": len(customers),
        })
        if self.request.GET.get("export"):
            ctx["_customers"] = customers
        return ctx

    def render_to_response(self, context, **kwargs):
        # If export was requested, build the Excel/PDF file instead of the page.
        if context.get("_customers") is not None:
            fmt = self.request.GET.get("export")
            header = ["Customer ID", "Name", "Username", "Email", "Phone", "Accounts",
                      "Branch", "Status", "Joined"]
            rows = [header]
            for c in context["_customers"]:
                rows.append([c.customer_code, c.full_name, c.username, c.email, c.phone,
                             c.accounts.count(), c.branch.name if c.branch else "",
                             "Active" if c.is_active else "Inactive",
                             c.created_at.strftime("%Y-%m-%d")])
            # Hand the rows to the shared writer (csv/excel/pdf).
            return export_dispatch(fmt, rows, "customer_report", title="Customer Report")
        return super().render_to_response(context, **kwargs)


class LoanReportView(StaffRequiredMixin, TemplateView):
    template_name = "reports/loan_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        loans = list(Loan.objects.select_related("customer").order_by("-applied_at"))
        ctx.update({
            "page_title": "Loan Report",
            "active_nav": "reports",
            "dashboard_home_url": self.dashboard_home_url,
            "current_role": self.role,
            "is_staff": self.is_staff,
            "loans": loans[:300],
            "count": len(loans),
            "portfolio": sum((l.principal_amount for l in loans if l.is_open), Decimal("0")),
        })
        if self.request.GET.get("export"):
            ctx["_loans"] = loans
        return ctx

    def render_to_response(self, context, **kwargs):
        if context.get("_loans") is not None:
            fmt = self.request.GET.get("export")
            header = ["Reference", "Customer", "Type", "Principal", "Rate %", "Tenure",
                      "EMI", "Paid", "Remaining", "Status", "Applied"]
            rows = [header]
            for l in context["_loans"]:
                rows.append([l.reference, l.customer.full_name, l.get_loan_type_display(),
                             f"{l.principal_amount}", f"{l.interest_rate}", l.tenure_months,
                             f"{l.emi_amount}", f"{l.amount_paid}", f"{l.remaining_amount}",
                             l.get_status_display(), l.applied_at.strftime("%Y-%m-%d")])
            return export_dispatch(fmt, rows, "loan_report", title="Loan Report")
        return super().render_to_response(context, **kwargs)
