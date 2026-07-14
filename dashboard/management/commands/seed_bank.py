"""Seed the database with realistic demo data for all three dashboards.

Usage:
    python manage.py seed_bank            # create data if missing
    python manage.py seed_bank --reset    # wipe domain data first, then seed

Safe to run repeatedly; it will not duplicate users that already exist.
"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Account, Branch
from customers.models import Customer
from dashboard.models import ActivityLog, Notification
from dashboard.services import deposit, transfer, withdraw
from employees.models import Employee
from loans.models import Loan, LoanRepayment
from transactions.models import Transaction


CUSTOMERS = [
    ("Ali Khan", "alikhan", "ali.khan@example.com", "Ali@12345", "35202-1234567-1", "03001234567", "Software Engineer", 180000),
    ("Ayesha Malik", "ayesham", "ayesha.malik@example.com", "Ayesha@123", "42101-2345678-2", "03011234568", "Accountant", 120000),
    ("Ahmed Raza", "ahmedraza", "ahmed.raza@example.com", "Ahmed@123", "61101-3456789-3", "03021234569", "DBA", 200000),
    ("Fatima Noor", "fatiman", "fatima.noor@example.com", "Fatima@123", "36601-4567890-4", "03031234570", "Teacher", 90000),
    ("Hassan Ali", "hassanali", "hassan.ali@example.com", "Hassan@123", "17301-5678901-5", "03041234571", "Civil Engineer", 160000),
    ("Maryam Ahmed", "maryama", "maryam.ahmed@example.com", "Maryam@123", "37405-6789012-6", "03051234572", "HR Officer", 110000),
    ("Umar Farooq", "umarf", "umar.farooq@example.com", "Umar@123", "33100-7890123-7", "03061234573", "Network Engineer", 170000),
    ("Zain Iqbal", "zainiqbal", "zain.iqbal@example.com", "Zain@123", "54400-8901234-8", "03071234574", "Data Analyst", 150000),
]


class Command(BaseCommand):
    help = "Seed demo data (branch, manager, employees, customers, accounts, transactions, loans)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing domain data first.")
        parser.add_argument("--employees", type=int, default=100, help="Number of employees to seed (excluding the manager).")
        parser.add_argument("--customers", type=int, default=100, help="Number of customers to seed.")

    def handle(self, *args, **options):
        reset = options["reset"]
        target_employees = options["employees"]
        target_customers = options["customers"]

        if reset:
            self.stdout.write("Resetting domain data...")
            LoanRepayment.objects.all().delete()
            Loan.objects.all().delete()
            Transaction.objects.all().delete()
            Account.objects.all().delete()
            Notification.objects.all().delete()
            ActivityLog.objects.all().delete()
            Employee.objects.all().delete()
            Customer.objects.all().delete()
            # Re-seeding Branch via get_or_create is fine.

        branch = self._seed_branch()
        manager = self._seed_manager(branch)
        employees = self._seed_employees(branch, target_employees)
        customers = self._seed_customers(branch, target_customers)
        self._seed_accounts_and_transactions(customers, branch, employees)
        self._seed_loans(customers, manager, employees)
        self._seed_activity(manager, employees, customers)


        self.stdout.write(self.style.SUCCESS("\nDemo data ready."))
        self.stdout.write("Login credentials:")
        self.stdout.write("  Branch Manager -> username: manager      password: Manager@123")
        self.stdout.write("  Employee       -> username: teller1       password: Teller@123")
        self.stdout.write("  Customer       -> username: alikhan       password: Ali@12345")

    # -- Seeders --------------------------------------------------------
    def _seed_branch(self) -> Branch:
        branch, _ = Branch.objects.get_or_create(
            code="BR-001",
            defaults=dict(
                name="Main Branch", city="Lahore",
                address="1 Mall Road, Lahore", phone="042-111-000-111",
                email="main@bankms.example",
            ),
        )
        self.stdout.write(f"Branch: {branch.name}")
        return branch

    def _seed_manager(self, branch) -> Employee:
        manager = Employee.objects.filter(username="manager").first()
        if not manager:
            manager = Employee(
                full_name="Sara Bank Manager", username="manager",
                email="manager@bankms.example", role=Employee.Role.MANAGER,
                position="Branch Manager", branch=branch, phone="03000000001",
            )
            manager.set_password("Manager@123")
            manager.save()
        else:
            manager.role = Employee.Role.MANAGER
            manager.branch = branch
            manager.save()
        self.stdout.write(f"Manager: {manager.full_name}")
        return manager

    def _seed_employees(self, branch, target_employees: int) -> list[Employee]:
        # Always create at least two baseline employees.
        specs = [
            ("Bilal Teller", "teller1", "teller1@bankms.example", "Teller@123", "Teller", True, False),
            ("Nadia Officer", "officer1", "officer1@bankms.example", "Officer@123", "Loan Officer", True, True),
        ]

        result: list[Employee] = []

        for full_name, username, email, pwd, position, can_rev, can_loan in specs:
            emp = Employee.objects.filter(username=username).first()
            if not emp:
                emp = Employee(
                    full_name=full_name,
                    username=username,
                    email=email,
                    role=Employee.Role.EMPLOYEE,
                    position=position,
                    branch=branch,
                    can_reverse_transactions=can_rev,
                    can_approve_loans=can_loan,
                )
                emp.set_password(pwd)
                emp.save()
            result.append(emp)

        # Generate remaining employees.
        occupations = ["Clerk", "Teller", "Officer", "Auditor", "Loan Assistant", "Compliance", "Risk Analyst"]
        for i in range(len(result), target_employees):
            username = f"employee{i+1:03d}"
            email = f"employee{i+1:03d}@bankms.example"
            full_name = f"Employee {i+1}"
            position = random.choice(occupations)
            can_rev = random.random() < 0.5
            can_loan = random.random() < 0.25

            emp = Employee.objects.filter(username=username).first()
            if not emp:
                emp = Employee(
                    full_name=full_name,
                    username=username,
                    email=email,
                    role=Employee.Role.EMPLOYEE,
                    position=position,
                    branch=branch,
                    can_reverse_transactions=can_rev,
                    can_approve_loans=can_loan,
                )
                emp.set_password("Employee@123")
                emp.save()
            elif not emp.branch:
                emp.branch = branch
                emp.save()

            result.append(emp)

        self.stdout.write(f"Employees: {len(result)}")
        return result

    def _seed_customers(self, branch, target_customers: int) -> list[Customer]:
        result: list[Customer] = []

        # Seed the predefined demo customers first.
        for full_name, username, email, pwd, cnic, phone, occupation, income in CUSTOMERS:
            cust = Customer.objects.filter(username=username).first()
            if not cust:
                cust = Customer(
                    full_name=full_name,
                    username=username,
                    email=email,
                    cnic=cnic,
                    phone=phone,
                    occupation=occupation,
                    monthly_income=Decimal(income),
                    branch=branch,
                    address=f"{branch.city}, Pakistan",
                )
                cust.set_password(pwd)
                cust.save()
            elif not cust.branch:
                cust.branch = branch
                cust.save()
            result.append(cust)

        # Generate remaining customers.
        first_names = ["Ali", "Ayesha", "Ahmed", "Fatima", "Hassan", "Maryam", "Umar", "Zain", "Sara", "Noor", "Hira", "Saad"]
        last_names = ["Khan", "Malik", "Raza", "Noor", "Ali", "Ahmed", "Farooq", "Iqbal", "Hussain", "Javed", "Akram", "Bashir"]
        occupations = ["Teacher", "Engineer", "Doctor", "Accountant", "Manager", "Developer", "Architect", "Business Owner", "Lawyer", "Designer"]

        for i in range(len(result), target_customers):
            idx = i + 1
            full_name = f"{random.choice(first_names)} {random.choice(last_names)} {idx}"
            username = f"customer{idx:03d}"
            email = f"customer{idx:03d}@bankms.example"
            pwd = "Customer@12345"
            cnic = f"{random.randint(10000, 99999)}-{random.randint(1000000, 9999999)}-{random.randint(1, 9)}"
            phone = f"03{random.randint(100000000, 999999999)}"
            occupation = random.choice(occupations)
            income = Decimal(random.randint(50_000, 250_000))

            cust = Customer.objects.filter(username=username).first()
            if not cust:
                cust = Customer(
                    full_name=full_name,
                    username=username,
                    email=email,
                    cnic=cnic,
                    phone=phone,
                    occupation=occupation,
                    monthly_income=income,
                    branch=branch,
                    address=f"{branch.city}, Pakistan",
                )
                cust.set_password(pwd)
                cust.save()
            elif not cust.branch:
                cust.branch = branch
                cust.save()

            result.append(cust)

        self.stdout.write(f"Customers: {len(result)}")
        return result


    def _seed_accounts_and_transactions(self, customers, branch, employees):
        teller = employees[0] if employees else None
        types = [Account.AccountType.SAVINGS, Account.AccountType.CURRENT, Account.AccountType.SALARY]
        created = 0
        for i, cust in enumerate(customers):
            if cust.accounts.exists():
                continue
            acc = Account.objects.create(
                customer=cust, branch=branch,
                account_type=types[i % len(types)],
                status=Account.Status.ACTIVE,
            )
            created += 1
            # Opening deposit + a spread of historical transactions.
            deposit(acc, Decimal(random.randint(40, 120) * 1000), employee=teller,
                    channel=Transaction.Channel.TELLER, description="Opening deposit")
            for _ in range(random.randint(4, 9)):
                if random.random() < 0.6:
                    deposit(acc, Decimal(random.randint(2, 30) * 1000), employee=teller,
                            channel=random.choice([Transaction.Channel.ONLINE, Transaction.Channel.ATM]),
                            description="Salary / income credit")
                else:
                    amt = Decimal(random.randint(1, 15) * 1000)
                    if amt < acc.available_balance:
                        withdraw(acc, amt, employee=teller,
                                 channel=random.choice([Transaction.Channel.ATM, Transaction.Channel.ONLINE]),
                                 description="ATM / bill payment")
            # Backdate transactions across the last 6 months for nicer charts.
            self._backdate_transactions(acc)

        # A couple of transfers between the first customers.
        accs = list(Account.objects.all()[:4])
        if len(accs) >= 2:
            try:
                transfer(accs[0], accs[1], Decimal("5000"), employee=teller,
                         description="Rent share")
                transfer(accs[2 % len(accs)], accs[3 % len(accs)], Decimal("2500"),
                         employee=teller, description="Gift")
            except Exception:  # pragma: no cover - defensive for low balances
                pass
        self.stdout.write(f"Accounts created: {created}")

    def _backdate_transactions(self, account):
        txns = list(account.transactions.all())
        now = timezone.now()
        for txn in txns:
            days_ago = random.randint(0, 175)
            Transaction.objects.filter(pk=txn.pk).update(
                created_at=now - timedelta(days=days_ago, hours=random.randint(0, 23))
            )

    def _seed_loans(self, customers, manager, employees):
        officer = next((e for e in employees if e.can_approve_loans), manager)
        if Loan.objects.exists():
            return
        specs = [
            (customers[0], Loan.LoanType.CAR, 800000, 14, 36, Loan.Status.ACTIVE),
            (customers[1], Loan.LoanType.PERSONAL, 300000, 18, 24, Loan.Status.PENDING),
            (customers[2], Loan.LoanType.HOME, 5000000, 11, 120, Loan.Status.UNDER_REVIEW),
            (customers[3], Loan.LoanType.EDUCATION, 400000, 9, 24, Loan.Status.APPROVED),
            (customers[4], Loan.LoanType.BUSINESS, 1200000, 16, 48, Loan.Status.REJECTED),
        ]
        for cust, ltype, principal, rate, tenure, status in specs:
            loan = Loan(
                customer=cust, account=cust.primary_account, loan_type=ltype,
                principal_amount=Decimal(principal), interest_rate=Decimal(rate),
                tenure_months=tenure, status=status,
                purpose=f"{loan_type_label(ltype)} financing",
            )
            if status in {Loan.Status.APPROVED, Loan.Status.ACTIVE, Loan.Status.REJECTED}:
                loan.reviewed_by = officer
                loan.approved_by = officer
                loan.decided_at = timezone.now()
            loan.save()
            if status == Loan.Status.ACTIVE:
                for _ in range(random.randint(2, 6)):
                    pay = loan.emi_amount
                    LoanRepayment.objects.create(loan=loan, amount=pay, recorded_by=officer)
                    loan.amount_paid = (loan.amount_paid or Decimal("0")) + pay
                loan.save(update_fields=["amount_paid"])
        self.stdout.write(f"Loans: {Loan.objects.count()}")

    def _seed_activity(self, manager, employees, customers):
        if ActivityLog.objects.exists():
            return
        ActivityLog.objects.create(actor_role="manager", actor_name=manager.full_name,
                                   employee=manager, category=ActivityLog.Category.AUTH,
                                   action="Signed in to the admin dashboard")
        for e in employees:
            ActivityLog.objects.create(actor_role="employee", actor_name=e.full_name,
                                       employee=e, category=ActivityLog.Category.AUTH,
                                       action="Signed in to the employee dashboard")
        for c in customers[:4]:
            ActivityLog.objects.create(actor_role="customer", actor_name=c.full_name,
                                       customer=c, category=ActivityLog.Category.AUTH,
                                       action="Signed in to online banking")
            Notification.objects.create(
                audience=Notification.Audience.CUSTOMER, customer=c,
                category=Notification.Category.SYSTEM,
                title="Welcome to BankMS", message="Your online banking is active.",
            )


def loan_type_label(value):
    return dict(Loan.LoanType.choices).get(value, "Loan")
