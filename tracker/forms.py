from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Category,Transaction,Profile

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username","email","password1","password2"]

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class":"form-control"})


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name","type","color"]
        widgets = {
            "name": forms.TextInput(attrs={"class":"form-control","placeholder":"e.g. Food,Salary"}),
            "type": forms.Select(attrs={"class":"form-select"}),
            "color":forms.TextInput(attrs={"type":"color","class":"form-control form-control-color"}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["category","amount","date","note"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control",
                                                "step": "0.01", "min": "0"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "note": forms.TextInput(attrs={"class": "form-control",
                                            "placeholder": "Optional note"}),
        }

    def __init__(self,*args,user=None,txn_type=None,**kwargs):
        super().__init__(*args,**kwargs)
        if user is not None and txn_type is not None:
            self.fields["category"].queryset = user.categories.filter(type=txn_type)

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150,required=False,widget=forms.TextInput(attrs={"class":"form-control"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class":"form-control"}), required=False)

    class Meta:
        model = Profile
        fields = ["currency","monthly_budget"]
        widgets = {
            "currency": forms.TextInput(attrs={"class":"form-control","maxlength":3}),
            "monthly_budget": forms.NumberInput(attrs={"class":"form-control","step":"0.01","min":"0"}),
        }
