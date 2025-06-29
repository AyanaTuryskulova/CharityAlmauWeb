from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .forms import ProductForm
from django.http import JsonResponse
from .models import Category, Product
from django.db import models 
from django.shortcuts import get_object_or_404

def onboarding_view(request):
    return render(request, 'onboarding.html')

@login_required
def home_view(request):
    return render(request, 'home.html')


@login_required
def add_product(request):
    main_categories = Category.objects.filter(parent__isnull=True)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            return redirect('home')
    else:
        form = ProductForm()

    return render(request, 'add_product.html', {
        'form': form,
        'main_categories': main_categories
    })

def get_subcategories(request, category_id):
    subcategories = Category.objects.filter(parent_id=category_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)

@login_required
def home_view(request):
    selected_category = request.GET.get('category')
    products = Product.objects.all()

    if selected_category:
        products = products.filter(
            models.Q(main_category_id=selected_category) |
            models.Q(subcategory_id=selected_category) |
            models.Q(sub_subcategory_id=selected_category)
        )

    main_categories = Category.objects.filter(parent__isnull=True)
    return render(request, 'home.html', {
        'products': products,
        'main_categories': main_categories,
        'selected_id': selected_category
    })

@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})



# Регистрация
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

# Вход
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# Выход
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
