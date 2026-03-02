# core/views.py

import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from django.db.utils import OperationalError
from django.urls import reverse, NoReverseMatch

from .models import Category, Product, ProductImage, TradeRequest, Favorite
from .forms import ProductForm
from .services.image_autofill import infer_product_from_image


def _get_favorite_ids(request):
    """Возвращает set id товаров, находящихся в избранном у пользователя."""
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return set()
    try:
        return set(
            Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    except OperationalError:
        return set()


def _ms_login_url():
    # 1) пробуем провайдер-специфичное имя
    try:
        return reverse('microsoft_login')
    except NoReverseMatch:
        pass
    # 2) пробуем общее имя старых версий
    try:
        return reverse('socialaccount_login', kwargs={'provider': 'microsoft'})
    except NoReverseMatch:
        pass
    # 3) последний надёжный вариант — прямой путь
    return '/accounts/microsoft/login/'


def login_view(request):
    return render(request, 'login.html')


def register_view(request):
    return render(request, 'register.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return HttpResponseBadRequest()


def onboarding_view(request):
    # Если пользователь аутентифицирован и уже прошёл онбординг,
    # по умолчанию перенаправляем на домашнюю страницу.
    # Но если в GET передан параметр force=1, показываем онбординг в любом случае.
    force = request.GET.get('force')
    if request.user.is_authenticated and not force and request.session.get('onboarded', False):
        return redirect('home')

    if request.method == 'POST':
        # Отмечаем в сессии, что пользователь прошёл онбординг
        request.session['onboarded'] = True
        return redirect('home')

    return render(request, 'onboarding.html')


def home_view(request):
    selected = request.GET.get('category')
    try:
        selected_id = int(selected) if selected else None
    except (ValueError, TypeError):
        selected_id = None

    q = (request.GET.get('q') or '').strip()

    qs = Product.objects.filter(is_approved=True).order_by('-created_at')
    if request.user.is_authenticated:
        qs = qs.exclude(user=request.user)
    if selected_id:
        qs = qs.filter(
            Q(main_category_id=selected_id) |
            Q(subcategory_id=selected_id) |
            Q(sub_subcategory_id=selected_id)
        )
    if q:
        q_lower = q.lower()
        # Фильтр в Python: регистронезависимый поиск для любого языка и БД
        product_list = list(qs)
        product_list = [
            p for p in product_list
            if q_lower in (p.title or '').lower() or q_lower in (p.description or '').lower()
        ]
        qs = product_list

    cats = Category.objects.filter(parent__isnull=True)
    return render(request, 'home.html', {
        'products': qs,
        'main_categories': cats,
        'selected_id': selected_id,
        'search_query': q,
        'favorite_ids': _get_favorite_ids(request),
    })


def free_list(request):
    selected = request.GET.get('category')
    try:
        selected_id = int(selected) if selected else None
    except (ValueError, TypeError):
        selected_id = None

    qs = Product.objects.filter(type='free', status='available', is_approved=True)
    if request.user.is_authenticated:
        qs = qs.exclude(user=request.user)

    if selected_id:
        qs = qs.filter(
            Q(main_category_id=selected_id) |
            Q(subcategory_id=selected_id) |
            Q(sub_subcategory_id=selected_id)
        )

    cats = Category.objects.filter(parent__isnull=True).prefetch_related('category_set')
    open_category_id = None
    if selected_id:
        for cat in cats:
            if cat.id == selected_id:
                open_category_id = cat.id
                break
            for child in cat.category_set.all():
                if child.id == selected_id:
                    open_category_id = cat.id
                    break
            if open_category_id:
                break

    return render(request, 'free.html', {
        'products': qs,
        'categories': cats,
        'selected_id': selected_id,
        'open_category_id': open_category_id,
        'favorite_ids': _get_favorite_ids(request),
    })


def exchange_list(request):
    selected = request.GET.get('category')
    try:
        selected_id = int(selected) if selected else None
    except (ValueError, TypeError):
        selected_id = None

    qs = Product.objects.filter(type='exchange', status='available', is_approved=True)
    if request.user.is_authenticated:
        qs = qs.exclude(user=request.user)

    if selected_id:
        qs = qs.filter(
            Q(main_category_id=selected_id) |
            Q(subcategory_id=selected_id) |
            Q(sub_subcategory_id=selected_id)
        )

    cats = Category.objects.filter(parent__isnull=True).prefetch_related('category_set')
    open_category_id = None
    if selected_id:
        for cat in cats:
            if cat.id == selected_id:
                open_category_id = cat.id
                break
            for child in cat.category_set.all():
                if child.id == selected_id:
                    open_category_id = cat.id
                    break
            if open_category_id:
                break

    return render(request, 'exchange.html', {
        'products': qs,
        'categories': cats,
        'selected_id': selected_id,
        'open_category_id': open_category_id,
        'favorite_ids': _get_favorite_ids(request),
    })


@login_required
def my_ads(request):
    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        remove_fav = request.POST.get('remove_fav')
        if delete_id:
            product = get_object_or_404(Product, id=delete_id, user=request.user)
            product.delete()
            messages.success(request, "Объявление удалено.")
        elif remove_fav:
            try:
                pid = int(remove_fav)
                fav = Favorite.objects.filter(user=request.user, product_id=pid).first()
                if fav:
                    fav.delete()
                    messages.success(request, "Удалено из избранного.")
            except (ValueError, TypeError, OperationalError):
                pass
        return redirect('my_ads')

    own_products = Product.objects.filter(user=request.user)
    favorites_available = True
    try:
        favorites_qs = Favorite.objects.filter(user=request.user).select_related('product').order_by('-created_at')
        favorite_products = [f.product for f in favorites_qs]
        fav_count = len(favorite_products)
    except OperationalError:
        favorite_products = []
        fav_count = 0
        favorites_available = False

    return render(request, 'my_ads.html', {
        'own_products': own_products,
        'favorite_products': favorite_products,
        'fav_count': fav_count,
        'favorites_available': favorites_available,
    })


@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, user=request.user)
    main_categories = Category.objects.filter(parent__isnull=True)
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
        'main_categories': main_categories,
    })


@login_required
def requests_view(request):
    if request.method == 'POST':
        req_id = request.POST['req_id']
        decision = request.POST['decision']
        tr = get_object_or_404(TradeRequest, id=req_id)

        if decision in ('accept', 'reject') and request.user == tr.owner and tr.status == 'pending':
            tr.status = 'accepted' if decision == 'accept' else 'rejected'
            tr.save()
        elif decision == 'cancel' and request.user == tr.requester and tr.status == 'pending':
            tr.status = 'cancelled'
            tr.save()
        elif decision == 'complete' and request.user == tr.requester and tr.status == 'accepted':
            tr.status = 'completed'
            tr.save()

        return redirect('requests')

    incoming = list(TradeRequest.objects.filter(owner=request.user).select_related('product', 'requester').order_by('-id'))
    outgoing = list(TradeRequest.objects.filter(requester=request.user).select_related('product', 'owner').order_by('-id'))

    # Гарантированно показываем только что созданную заявку на аренду (из сессии)
    last_rent_id = request.session.pop('last_rent_request_id', None)
    if last_rent_id:
        try:
            tr = TradeRequest.objects.filter(id=last_rent_id, requester=request.user).select_related('product', 'owner').first()
            if tr and tr not in outgoing:
                outgoing = [tr] + [r for r in outgoing if r.id != tr.id]
        except Exception:
            pass

    response = render(request, 'requests.html', {
        'incoming': incoming,
        'outgoing': outgoing,
    })
    # Отключаем кэш, чтобы после редиректа с «Арендовать» всегда показывался актуальный список
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response


@login_required
def add_product(request):
    main_categories = Category.objects.filter(parent__isnull=True)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            # До 5 фото: images_0 — основное, images_1..4 — ProductImage
            files = []
            for i in range(5):
                f = request.FILES.get('images_%d' % i)
                if f:
                    files.append(f)
            if not files:
                form.add_error(None, 'Добавьте хотя бы одно фото.')
                return render(request, 'add_product.html', {
                    'form': form,
                    'main_categories': main_categories,
                })
            if len(files) > 5:
                form.add_error(None, 'Можно загрузить не более 5 фото.')
                return render(request, 'add_product.html', {
                    'form': form,
                    'main_categories': main_categories,
                })
            p = form.save(commit=False)
            p.user = request.user
            p.is_approved = False
            p.image = files[0]

            inference = infer_product_from_image(files[0])
            if not (p.title or '').strip():
                p.title = (inference.title or '').strip()
            if not p.main_category and inference.main_category:
                p.main_category = inference.main_category
                p.subcategory = None
                p.sub_subcategory = None
            if not (p.title or '').strip():
                p.title = 'Предмет'

            if p.type == 'rental':
                duration = request.POST.get('rental_duration', '').strip()
                location = request.POST.get('location', '').strip()
                extra = []
                if duration:
                    extra.append('Длительность аренды: %s' % duration)
                if location:
                    extra.append('Расположение: %s' % location)
                if extra:
                    p.description = (p.description or '').rstrip() + '\n\n' + '\n'.join(extra)
            p.save()
            for i, f in enumerate(files[1:5]):
                ProductImage.objects.create(product=p, image=f, order=i)
            messages.info(request, "Ваше объявление отправлено на модерацию.")
            return redirect('my_ads')
    else:
        form = ProductForm(initial={'type': 'rental'})
    return render(request, 'add_product.html', {
        'form': form,
        'main_categories': main_categories
    })


@login_required
def infer_product_image(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    image_file = request.FILES.get('image') or request.FILES.get('images_0')
    if not image_file:
        return JsonResponse({
            'title': '',
            'main_category_id': None,
            'main_category_name': '',
        })

    try:
        result = infer_product_from_image(image_file)
        return JsonResponse({
            'title': result.title or '',
            'main_category_id': result.main_category.id if result.main_category else None,
            'main_category_name': result.main_category.name if result.main_category else '',
            'score': result.score,
            'raw_label': result.raw_label or '',
        })
    except Exception:
        logging.getLogger(__name__).exception("infer_product_image failed")
        return JsonResponse({
            'title': '',
            'main_category_id': None,
            'main_category_name': '',
            'error': 'inference_failed',
        })


def get_subcategories(request, category_id):
    subs = Category.objects.filter(parent_id=category_id).values('id', 'name')
    return JsonResponse(list(subs), safe=False)


@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Только автор может просматривать свой неободренный товар
    if not product.is_approved and product.user != request.user:
        messages.error(request, "Этот товар ещё не прошёл модерацию.")
        return redirect('home')

    try:
        in_favorites = Favorite.objects.filter(user=request.user, product=product).exists()
    except OperationalError:
        in_favorites = False
    # Список всех фото: основное + доп. (для галереи без пустых слотов)
    product_images = []
    if product.image:
        product_images.append(product.image)
    for extra in product.extra_images_list():
        if getattr(extra, 'image', None):
            product_images.append(extra.image)
    return render(request, 'product_detail.html', {
        'product': product,
        'in_favorites': in_favorites,
        'product_images': product_images,
    })


@login_required
def favorite_toggle(request, product_id):
    """Добавить или убрать товар из избранного."""
    product = get_object_or_404(Product, id=product_id)
    if product.user == request.user:
        messages.error(request, "Нельзя добавить в избранное свой товар.")
        return redirect('product_detail', product_id=product_id)

    try:
        fav, created = Favorite.objects.get_or_create(user=request.user, product=product)
        if not created:
            fav.delete()
            messages.success(request, "Удалено из избранного.")
        else:
            messages.success(request, "Добавлено в избранное.")
    except OperationalError:
        messages.info(request, "Избранное пока недоступно. Выполните: python manage.py migrate")

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('product_detail', args=[product_id])
    return redirect(next_url)


@login_required
def product_action(request, product_id, action):
    product = get_object_or_404(Product, id=product_id)

    if product.user == request.user:
        messages.error(request, "Нельзя запросить свой же товар.")
        return redirect('home')

    if not product.is_approved:
        messages.error(request, "Этот товар ещё не одобрен.")
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
