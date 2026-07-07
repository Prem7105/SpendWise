from django.test import TestCase
from datetime import date
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
        self.assertNotContains(resp,"50")
    
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