import csv
import json
from datetime import date

from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.utils import timezone
from .models import Profile
from .forms import RegisterForm,CategoryForm,TransactionForm,ProfileForm
from .models import Category,Transaction

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]

#AUTH
def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = form.cleaned_data.get("email","")
            user.save() 
            login(request,user)
            _seed_starter_categories(user)
            messages.success(request,"Welcome to Spendwise! Your account is ready.")
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request,"registeration/register.html",{"form",form})

def _seed_starter_categories(user):
    defaults = [
        ("Salary", "INCOME", "#1cc88a"),
        ("Freelance", "INCOME", "#36b9cc"),
        ("Food", "EXPENSE", "#e74a3b"),
        ("Rent", "EXPENSE", "#4e73df"),
        ("Transport", "EXPENSE", "#f6c23e"),
        ("Shopping", "EXPENSE", "#a020f0"),
    ]
    for name,type_,color in defaults:
        Category.objects.get_or_create(user=user,name=name,type=type_,defaults={"color":color})

#   Dashboard

@login_required
def dashboard(request):
    txns = request.user.transactions.all()

    total_income = txns.filter(type="INCOME").aggregate(s=Sum("amount"))["s"] or 0
    total_expense = txns.filter(type="EXPENSE").aggregate(s=Sum("amount"))["s"] or 0
    balance = total_income - total_expense

    today = timezone.now().date()
    month_txns=txns.filter(date__year=today.year,date__month=today.month)
    month_income=month_txns.filter(type="INCOME").aggregate(s=Sum("amount"))["s"] or 0
    month_expense=month_txns.filter(type="EXPENSE").aggregate(s=Sum("amount"))["s"] or 0

    profile, created = Profile.objects.get_or_create(user=request.user)
    budget = profile.monthly_budget
    budget_pct = 0
    if budget and budget > 0:
        budget_pct=min(round(float(month_expense) / float(budget) * 100), 100)
    
    by_cat = (txns.filter(type="EXPENSE")
                .values("category__name","category__color")
                .annotate(total=Sum("amount")).order_by("-total"))
    cat_labels = [c["category__name"] for c in by_cat]
    cat_values = [float(c["total"]) for c in by_cat]
    cat_colors = [c["category__color"] for c in by_cat]

    month_labels,income_series,expense_series = [],[],[]
    y,m=today.year,today.month
    months = []
    for _ in range(6):
        months.append((y,m))
        m-=1
        if m==0:
            m=12
            y-=1
    for (yy,mm) in reversed(months):
        month_labels.append(f"{MONTH_NAMES[mm-1]} {str(yy)[2:]}")
        mt = txns.filter(date__year=yy,date__month=mm)
        income_series.append(float(mt.filter(type="INCOME").aggregate(s=Sum("amount"))["s"] or 0))
        expense_series.append(float(mt.filter(type="EXPENSE").aggregate(s=Sum("amount"))["s"] or 0))

    context={
        "total_income":total_income,"total_expense":total_expense,"balance":balance,
        "month_income":month_income,"month_expense":month_expense,"budget":budget,
        "budget_pct":budget_pct,
        "recent":txns.select_related("category")[:8],"has_data":txns.exists(),
        "cat_labels": json.dumps(cat_labels),"cat_values":json.dumps(cat_values),
        "cat_colors":json.dumps(cat_colors),"month_labels":json.dumps(month_labels),
        "income_series":json.dumps(income_series),"expense_series":json.dumps(expense_series),
    }
    return render(request,"tracker/dashboard.html",context)

# TRANSACTIONS
@login_required
def transaction_list(request,txn_type):
    qs = request.user.transactions.filter(type=txn_type).select_related("category")
    start = request.GET.get("start")
    end = request.GET.get("end")
    category = request.GET.get("category")
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs=qs.filter(date__lte=end)
    if category:
        qs=qs.filter(category_id=category)
    total=qs.aggregate(s=Sum("amount"))["s"] or 0
    categories = request.user.categories.filter(type=txn_type)
    return render(request,"tracker/transaction_list.html",{
        "transactions":qs,"total":total,"txn_type":txn_type,
        "categories":categories,
        "filters":{"start":start or "","end":end or "","category":category or ""},
    })

@login_required
def transaction_create(request,txn_type):
    txn_type=txn_type.upper()
    if txn_type not in ("INCOME","EXPENSE"):
        return redirect("dashboard")
    if request.method == "POST":
        form=TransactionForm(request.POST,user=request.user,txn_type=txn_type)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.user=request.user
            txn.type=txn_type
            txn.save()
            messages.success(request,f"{txn_type.title()} of {txn.amount} addded.")
            return redirect("income" if txn_type=="INCOME" else "expense")
    else:
        form=TransactionForm(user=request.user,txn_type=txn_type,
                            initial={"date":date.today()})
    return render(request,"tracker/transaction_form.html",
                    {"form":form,"txn_type":txn_type,"mode":"Add"})

@login_required
def transaction_update(request,pk):
    txn= get_object_or_404(Transaction,pk=pk,user=request.user)
    if request.method=="POST":
        form=TransactionForm(request.POST,instance=txn,user=request.user,txn_type=txn.type)
        if form.is_valid():
            form.save()
            messages.success(request,"Transaction updated")
            return redirect("income" if txn.type=="INCOME" else "expense")
    else:
        form=TransactionForm(instance=txn,user=request.user,txn_type=txn.type)
    return render(request,"tracker/transaction_form.html",
                    {"form":form,"txn_type":txn.type,"mode":"Edit"})

@login_required
def transaction_delete(request,pk):
    txn = get_object_or_404(Transaction,pk=pk,user=request.user)
    if request.method == "POST":
        redirect_to = "income" if txn.type == "INCOME" else "expense"
        txn.delete()
        messages.success(request,"Transaction deleted")
        return redirect(redirect_to)
    return render(request,"tracker/transaction_confirm_delete.html",{"txn":txn})

# Categories

@login_required
def category_list(request):
    if request.method=="POST":
        form=CategoryForm(request.POST)
        if form.is_valid():
            cat=form.save(commit=False)
            cat.user=request.user
            if request.user.categories.filter(name=cat.name,type=cat.type).exists():
                messages.error(request,"You already have a category with name and type")
            else:
                cat.save()
                messages.success(request,"Category addded")
            return redirect("category_list")
    else:
        form=CategoryForm()
    categories=request.user.categories.all()
    return render(request,"tracker/category_list.html",
                    {"categories":categories,"form":form})

@login_required
def category_update(request,pk):
    cat=get_object_or_404(Category,pk=pk,user=request.user)
    if request.method=="POST":
        form=CategoryForm(request.POST,instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request,"Category update")
            return redirect("category_list")
    else:
        form=CategoryForm(instance=cat)
    return render(request,"tracker/category_form.html",{"form":form,"cat":cat})

@login_required
def category_delete(request,pk):
    cat=get_object_or_404(Category,pk=pk,user=request.user)
    if request.method=="POST":
        if cat.transactions.exists():
            messages.error(request,"Cannot delete as this category has transaction")
        else:
            cat.delete()
            messages.success(request,"Category deleted")
        return redirect("category_list")
    return render(request,"tracker/category_confirm_delete.html",{"cat":cat})

#       REPORT

@login_required
def reports(request):
    today=timezone.now().date()
    try:
        year=int(request.GET.get("year",today.year))
        month=int(request.GET.get("month",today.month))
    except (TypeError,ValueError):
        year,month=today.year,today.month
    month=min(max(month,1),12)

    txns=request.user.transactions.filter(date__year=year,date__month=month)
    income=txns.filter(type="INCOME").aggregate(s=Sum("amount"))["s"] or 0
    expense=txns.filter(type="EXPENSE").aggregate(s=Sum("amount"))["s"] or 0
    by_cat=(txns.filter(type="EXPENSE").values("category__name","category__color")
            .annotate(total=Sum("amount")).order_by("-total"))
    
    return render(request,"tracker/reports.html",{
        "year":year,"month":month,"month_name":MONTH_NAMES[month-1],
        "income":income,"expense":expense,"balance":income-expense,
        "by_cat":by_cat,"transactions":txns.select_related("category"),
        "months":list(enumerate(MONTH_NAMES,start=1)),
        "years":list(range(today.year-3,today.year+1)),
    })

# CSV Export
    
@login_required
def export_csv(request):
    qs=request.user.transactions.select_related("category").all()
    if request.GET.get("type"):
        qs=qs.filter(type=request.GET["type"])
    if request.GET.get("start"):
        qs=qs.filter(date__gte=request.GET["start"])
    if request.GET.get("end"):
        qs=qs.filter(date__lte=request.GET["end"])
    if request.GET.get("category"):
        qs=qs.filter(category_id=request.GET["category"])

    response= HttpResponse(content_type="texts/csv")
    response["content-disposition"]='attachment;filename="spendwise_transaction.csv"'
    writer = csv.writer(response)
    writer.writerow(["Date","Type","Category","Amount","Note"])
    for t in qs:
        writer.writerow([t.date,t.type,t.category,t.amount,t.note])
    return response

# Profile

@login_required
def profile(request):
    prof=request.user.profile
    if request.method=="POST":
        form=ProfileForm(request.POST,instance=prof)
        if form.is_valid():
            form.save()
            request.user.first_name=form.cleaned_data.get("first_name","")
            request.user.email=form.cleaned_data.get("email","")
            request.user.save()
            messages.success(request,"Profile updated")
            return redirect("profile")
    else:
        form=ProfileForm(instance=prof,initial={
            "first_name":request.user.first_name,"email":request.user.email})
    return render(request,"tracker/profile.html",{"form":form})
