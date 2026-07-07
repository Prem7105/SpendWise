from django.contrib import admin
from .models import Profile, Category,Transaction

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",'type','user','color')
    list_filter = ('type',)
    search_fields = ("name",)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display=("date","type","category","amount","user")
    list_filter=("type","date")
    search_fields = ("note",)

admin.site.register(Profile)
