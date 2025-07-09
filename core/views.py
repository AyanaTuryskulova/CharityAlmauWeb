# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q

from .models import Category, Product, TradeRequest
from .forms import ProductForm


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Сразу пометим, что онбординг не пройден
            request.session['onboarded'] = False
            return redirect('onboarding')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Сбросим флаг онбординга, чтобы показать его после входа
            request.session['onboarded'] = False
            return redirect('onboarding')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return HttpResponseBadRequest()


@login_required
def onboarding_view(request):
    # Если уже прошёл — сразу на home
    if request.session.get('onboarded', False):
        return redirect('home')

    if request.method == 'POST':
        request.session['onboarded'] = True
        return redirect('home')

    return render(request, 'onboarding.html')



@login_required
def home_view(request):
    # Если онбординг не пройден, перенаправляем на него
    if not request.session.get('onboarded', False):
        return redirect('onboarding')

    selected = request.GET.get('category')
    try:
        selected_id = int(selected) if selected else None
    except (ValueError, TypeError):
        selected_id = None

    qs = Product.objects.exclude(user=request.user)
    if selected_id:
        qs = qs.filter(
            Q(main_category_id=selected_id) |
            Q(subcategory_id=selected_id) |
            Q(sub_subcategory_id=selected_id)
        )

    cats = Category.objects.filter(parent__isnull=True)
    return render(request, 'home.html', {
        'products': qs,
        'main_categories': cats,
        'selected_id': selected_id,
    })


@login_required
def my_ads(request):
    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        if delete_id:
            product = get_object_or_404(Product, id=delete_id, user=request.user)
            product.delete()
            messages.success(request, "Объявление удалено.")
        return redirect('my_ads')

    own_products = Product.objects.filter(user=request.user)
    return render(request, 'my_ads.html', {
        'own_products': own_products
    })


@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, user=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Объявление обновлено.")
            return redirect('my_ads')
    else:
        form = ProductForm(instance=product)
    return render(request, 'edit_product.html', {
        'form': form,
        'product': product,
    })


@login_required
def requests_view(request):
    if request.method == 'POST':
        req_id = request.POST['req_id']
        decision = request.POST['decision']
        tr = get_object_or_404(TradeRequest, id=req_id)

        if decision in ('accept','reject') and request.user == tr.owner and tr.status=='pending':
            tr.status = 'accepted' if decision=='accept' else 'rejected'
            tr.save()
        elif decision=='cancel' and request.user==tr.requester and tr.status=='pending':
            tr.status = 'cancelled'; tr.save()
        elif decision=='complete' and request.user==tr.requester and tr.status=='accepted':
            tr.status = 'completed'; tr.save()

        return redirect('requests')

    incoming = TradeRequest.objects.filter(owner=request.user).select_related('product','requester')
    outgoing = TradeRequest.objects.filter(requester=request.user).select_related('product','owner')
    return render(request, 'requests.html', {
        'incoming': incoming,
        'outgoing': outgoing,
    })


@login_required
def add_product(request):
    main_categories = Category.objects.filter(parent__isnull=True)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save(commit=False)
            p.user = request.user
            p.save()
            return redirect('home')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {
        'form': form,
        'main_categories': main_categories
    })


def get_subcategories(request, category_id):
    subs = Category.objects.filter(parent_id=category_id).values('id', 'name')
    return JsonResponse(list(subs), safe=False)


@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})


@login_required
def product_action(request, product_id, action):
    product = get_object_or_404(Product, id=product_id)
    if product.user == request.user:
        messages.error(request, "Нельзя запросить свой же товар.")
        return redirect('home')

    tr = TradeRequest.objects.create(
        product=product,
        requester=request.user,
        owner=product.user,
        action=action
    )
    if action == 'take':
        product.status = 'taken'
    else:
        product.status = 'exchanged'
    product.save()

    messages.success(request, "Заявка отправлена!")
    return redirect('requests')
