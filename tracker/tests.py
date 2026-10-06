from django.test import TestCase
import csv
import io
import json
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Category,Transaction,Profile

# Create your tests here.

class ProfileSignalTests(TestCase):
    def test_profile_created_with_user(self):
        user = User.objects.create_user("prem",password="123456")
        self.assertTrue(Profile.objects.filter(user=user).exists())

class DataIsolationTests(TestCase):
    def setUp(self):
        self.prem=User.objects.create_user("prem",password="123456")
        self.yash=User.objects.create_user("yash",password="123456")
        self.yash_cat=Category.objects.create(user=self.yash,name="Food",type="EXPENSE")
        Transaction.objects.create(user=self.yash,category=self.yash_cat,type="EXPENSE",
                                    amount=Decimal("100"),date=date.today())

    def test_prem_cannot_see_yashs_transaction(self):
        self.client.login(username="prem",password="123456")
        resp = self.client.get(reverse("expense"))
        self.assertEqual(resp.status_code,200)
        self.assertNotContains(resp,"100.00")
    
    def test_prem_cannot_delete_yashs_transaction(self):
        self.client.login(username="prem",password="123456")
        yash_txn=Transaction.objects.get(user=self.yash)
        resp=self.client.post(reverse("transaction_delete",args=[yash_txn.id]))
        self.assertEqual(resp.status_code,404)
        self.assertTrue(Transaction.objects.filter(id=yash_txn.id).exists())

class AuthRedirectTests(TestCase):

    def test_dashboard_requires_login(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)


class LoginFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("login-user", password="test-password-123")

    def login_to_dashboard(self):
        response = self.client.post(reverse("login"), {
            "username": self.user.username,
            "password": "test-password-123",
        }, follow=True)
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTemplateUsed(response, "tracker/dashboard.html")
        return response

    def test_login_with_empty_dashboard(self):
        response = self.login_to_dashboard()
        self.assertContains(response, "No Transactions Yet")

    def test_login_with_transactions(self):
        category = Category.objects.create(user=self.user, name="Food", type="EXPENSE")
        Transaction.objects.create(user=self.user, category=category, type="EXPENSE",
                                   amount=Decimal("100.00"), date=date.today())
        response = self.login_to_dashboard()
        self.assertEqual(response.context["total_expense"], Decimal("100.00"))
        self.assertContains(response, "Recent Transactions")

    def test_login_repairs_missing_profile(self):
        Profile.objects.filter(user=self.user).delete()
        self.login_to_dashboard()
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)

    def test_login_preserves_existing_profile_settings(self):
        Profile.objects.filter(user=self.user).update(
            currency="USD", monthly_budget=Decimal("500.00"))
        self.login_to_dashboard()
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.currency, "USD")
        self.assertEqual(profile.monthly_budget, Decimal("500.00"))

    def test_profile_page_repairs_missing_profile_in_existing_session(self):
        self.client.force_login(self.user)
        Profile.objects.filter(user=self.user).delete()
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_registration_redirects_to_dashboard(self):
        response = self.client.post(reverse("register"), {
            "username": "new-user",
            "email": "new-user@example.com",
            "password1": "new-account-password-123",
            "password2": "new-account-password-123",
        }, follow=True)
        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(username="new-user")
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        self.assertEqual(user.categories.count(), 6)


class FeatureFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("owner", password="test-password-123")
        cls.other = User.objects.create_user("other", password="test-password-123")
        cls.food = Category.objects.create(user=cls.user, name="Food", type="EXPENSE")
        cls.salary = Category.objects.create(user=cls.user, name="Salary", type="INCOME")
        cls.private = Category.objects.create(user=cls.other, name="Private", type="EXPENSE")
        cls.expense = Transaction.objects.create(user=cls.user, category=cls.food,
            type="EXPENSE", amount="100.00", date=date.today(), note="Lunch, coffee")
        cls.income = Transaction.objects.create(user=cls.user, category=cls.salary,
            type="INCOME", amount="1000.00", date=date.today())
        cls.private_txn = Transaction.objects.create(user=cls.other, category=cls.private,
            type="EXPENSE", amount="777.00", date=date.today(), note="Private note")

    def setUp(self):
        self.client.force_login(self.user)

    def test_all_pages_render(self):
        routes = [(name, []) for name in (
            "dashboard", "income", "expense", "category_list", "reports", "profile")]
        routes += [("transaction_create", [kind]) for kind in ("INCOME", "EXPENSE")]
        routes += [("transaction_update", [self.expense.pk]),
                   ("transaction_delete", [self.expense.pk]),
                   ("category_update", [self.food.pk]),
                   ("category_delete", [self.food.pk])]
        for name, args in routes:
            with self.subTest(route=name, args=args):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)

    def test_transaction_create_edit_delete(self):
        for kind, category, destination in (
            ("INCOME", self.salary, "income"), ("EXPENSE", self.food, "expense")):
            with self.subTest(kind=kind):
                data = {"category": category.pk, "amount": "45.67",
                        "date": date.today().isoformat(), "note": "New entry"}
                response = self.client.post(reverse("transaction_create", args=[kind]), data)
                self.assertRedirects(response, reverse(destination))
                txn = Transaction.objects.get(user=self.user, note="New entry")
                data.update(amount="67.89", note="Updated entry")
                response = self.client.post(reverse("transaction_update", args=[txn.pk]), data)
                self.assertRedirects(response, reverse(destination))
                txn.refresh_from_db()
                self.assertEqual(txn.amount, Decimal("67.89"))
                response = self.client.get(reverse("transaction_delete", args=[txn.pk]))
                self.assertTemplateUsed(response, "tracker/transaction_confirm_delete.html")
                self.assertTrue(Transaction.objects.filter(pk=txn.pk).exists())
                response = self.client.post(reverse("transaction_delete", args=[txn.pk]))
                self.assertRedirects(response, reverse(destination))
                self.assertFalse(Transaction.objects.filter(pk=txn.pk).exists())
                self.assertTrue(Category.objects.filter(pk=category.pk).exists())

    def test_category_create_edit_delete(self):
        data = {"name": "Travel", "type": "EXPENSE", "color": "#123456"}
        self.assertRedirects(self.client.post(reverse("category_list"), data), reverse("category_list"))
        category = Category.objects.get(user=self.user, name="Travel")
        data["name"] = "Trips"
        self.assertRedirects(self.client.post(reverse("category_update", args=[category.pk]), data),
                             reverse("category_list"))
        category.refresh_from_db()
        self.assertEqual(category.name, "Trips")
        self.assertRedirects(self.client.post(reverse("category_delete", args=[category.pk])),
                             reverse("category_list"))
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_used_category_cannot_be_deleted(self):
        response = self.client.post(reverse("category_delete", args=[self.food.pk]), follow=True)
        self.assertContains(response, "Cannot delete")
        self.assertTrue(Category.objects.filter(pk=self.food.pk).exists())

    def test_duplicate_category_edit_is_validation_error(self):
        duplicate = Category.objects.create(user=self.user, name="Dining", type="EXPENSE")
        response = self.client.post(reverse("category_update", args=[duplicate.pk]), {
            "name": "Food", "type": "EXPENSE", "color": "#123456"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        duplicate.refresh_from_db()
        self.assertEqual(duplicate.name, "Dining")

    def test_used_category_type_cannot_change(self):
        response = self.client.post(reverse("category_update", args=[self.food.pk]), {
            "name": "Food", "type": "INCOME", "color": "#123456"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.food.refresh_from_db()
        self.assertEqual(self.food.type, "EXPENSE")

    def test_dashboard_totals_charts_and_recent_order(self):
        old = Transaction.objects.create(user=self.user, category=self.food, type="EXPENSE",
            amount="20.00", date=date.today() - timedelta(days=400))
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["total_income"], Decimal("1000.00"))
        self.assertEqual(response.context["total_expense"], Decimal("120.00"))
        self.assertEqual(response.context["balance"], Decimal("880.00"))
        self.assertEqual(response.context["month_expense"], Decimal("100.00"))
        self.assertEqual(json.loads(response.context["cat_values"]), [120.0])
        self.assertEqual(len(json.loads(response.context["month_labels"])), 6)
        self.assertEqual(json.loads(response.context["expense_series"])[-1], 100.0)
        self.assertEqual(list(response.context["recent"])[-1].pk, old.pk)

    def test_profile_currency_budget_and_name(self):
        response = self.client.post(reverse("profile"), {"first_name": "Tester",
            "email": "tester@example.com", "currency": "USD", "monthly_budget": "200.00"})
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Tester")
        self.assertEqual(self.user.email, "tester@example.com")
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "USD")
        self.assertContains(response, "Tester")
        self.assertEqual(response.context["budget_pct"], 50)

    def test_monthly_report_totals(self):
        response = self.client.get(reverse("reports"), {
            "year": date.today().year, "month": date.today().month})
        self.assertEqual(response.context["income"], Decimal("1000.00"))
        self.assertEqual(response.context["expense"], Decimal("100.00"))
        self.assertEqual(response.context["balance"], Decimal("900.00"))
        self.assertNotContains(response, "Private note")

    def test_filters_and_csv_export(self):
        filters = {"start": date.today().isoformat(), "end": date.today().isoformat(),
                   "category": self.food.pk, "type": "EXPENSE"}
        response = self.client.get(reverse("expense"), filters)
        self.assertEqual(list(response.context["transactions"]), [self.expense])
        response = self.client.get(reverse("export_csv"), filters)
        self.assertEqual(response["Content-Type"], "text/csv")
        rows = list(csv.reader(io.StringIO(response.content.decode())))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][2:], ["Food", "100.00", "Lunch, coffee"])
        self.assertNotIn("Private note", response.content.decode())

    def test_other_users_records_are_inaccessible(self):
        for route, pk in (("transaction_update", self.private_txn.pk),
                          ("transaction_delete", self.private_txn.pk),
                          ("category_update", self.private.pk), ("category_delete", self.private.pk)):
            for method in (self.client.get, self.client.post):
                with self.subTest(route=route, method=method.__name__):
                    self.assertEqual(method(reverse(route, args=[pk])).status_code, 404)

    def test_invalid_transaction_categories_are_rejected(self):
        for category in (self.private, self.salary):
            with self.subTest(category=category.name):
                response = self.client.post(reverse("transaction_create", args=["EXPENSE"]), {
                    "category": category.pk, "amount": "10", "date": date.today().isoformat()})
                self.assertEqual(response.status_code, 200)
                self.assertIn("category", response.context["form"].errors)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 2)

    def test_logout_blocks_authenticated_pages(self):
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))
        for name in ("dashboard", "income", "expense", "category_list", "reports", "profile", "export_csv"):
            with self.subTest(route=name):
                self.assertRedirects(self.client.get(reverse(name)),
                                     reverse("login") + "?next=" + reverse(name))
