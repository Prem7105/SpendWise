from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    """Extra per-user settings on top of the built-in User."""
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    currency = models.CharField(max_length=3,default="INR")
    monthly_budget = models.DecimalField(
        max_digits=10,decimal_places=2,null=True,blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class Category(models.Model):
    INCOME, EXPENSE = "INCOME", "EXPENSE"
    TYPE_CHOICES = [(INCOME,"Income"), (EXPENSE, "Expense")]

    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="categories")
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES)
    color = models.CharField(max_length=7,default="#4e73df")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user','name','type')
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.type})"

class Transaction(models.Model):
    INCOME, EXPENSE="INCOME", 'EXPENSE'
    TYPE_CHOICES = [(INCOME,"Income"), (EXPENSE, "Expense")]

    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="transactions")
    category = models.ForeignKey("Category",on_delete=models.PROTECT, related_name="transactions")
    type = models.CharField(max_length=7,choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    date = models.DateField()
    note = models.CharField(max_length=255,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "-created_at"]
    
    def __str__(self):
        return f"{self.type} {self.amount} on {self.date}"
        