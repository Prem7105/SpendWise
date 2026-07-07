import random
from datetime import date,timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from tracker.models import Category,Transaction

class Command(BaseCommand):
    help = "Seed a demo user with sample categories and transactions."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="demo", defaults={"email": "demo@spendwise.app"})
        if created:
            user.set_password("demo12345"); user.save()
        user.transactions.all().delete(); user.categories.all().delete()

        income_cats = [("Salary", "#1cc88a"), ("Freelance", "#36b9cc")]
        expense_cats = [("Food", "#e74a3b"), ("Rent", "#4e73df"), ("Transport", "#f6c23e"),
                        ("Shopping", "#a020f0"), ("Bills", "#fd7e14")]
        cats = {}
        for name, color in income_cats:
            cats[name] = Category.objects.create(user=user, name=name, type="INCOME", color=color)
        for name, color in expense_cats:
            cats[name] = Category.objects.create(user=user, name=name, type="EXPENSE", color=color)

        today = date.today(); count = 0
        for months_ago in range(6):
            base = today.replace(day=1) - timedelta(days=months_ago * 30)
            Transaction.objects.create(user=user, category=cats["Salary"], type="INCOME",
                                        amount=Decimal("50000"), date=base, note="Monthly salary"); count += 1
            if random.random() < 0.5:
                Transaction.objects.create(user=user, category=cats["Freelance"], type="INCOME",
                                            amount=Decimal(random.randrange(5000, 20000)),
                                            date=base + timedelta(days=random.randint(1, 20)), note="Side project"); count += 1
            for _ in range(random.randint(6, 12)):
                name = random.choice([c[0] for c in expense_cats])
                Transaction.objects.create(user=user, category=cats[name], type="EXPENSE",
                    amount=Decimal(random.randrange(200, 8000)),
                    date=base + timedelta(days=random.randint(0, 27)), note=""); count += 1
        self.stdout.write(self.style.SUCCESS(
            f"Seeded demo user (login: demo / demo12345) with {count} transactions."))