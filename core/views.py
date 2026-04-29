# core/views.py

import logging
import json
import re
import threading

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q, Max
from django.db import transaction
from django.db.utils import OperationalError
from django.urls import reverse, NoReverseMatch
from django.utils.translation import check_for_language
from django.utils.translation import gettext as _
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.conf import settings as django_settings

from .models import Category, Product, ProductImage, TradeRequest, Favorite, Chat, Message, PushSubscription, RentItem
from .forms import ProductForm
from .services.image_autofill import infer_product_from_image
from .notifications import notify_trade_request
from .email_utils import notify_new_message


def _notify_trade_request_async(product, requester, action):
    # Запускает отправку уведомления о заявке в отдельном потоке и ничего не возвращает.
    """Sends trade-request notifications in background to avoid blocking redirect."""
    def _run():
        try:
            notify_trade_request(product=product, requester=requester, action=action)
        except Exception:
            logger = logging.getLogger(__name__)
            logger.exception("Failed to send trade request notification")

    threading.Thread(target=_run, daemon=True).start()


def switch_language(request, lang_code):
    # Переключает язык интерфейса через cookie и возвращает redirect на предыдущую страницу.
    """Переключает язык интерфейса через cookie и перенаправляет обратно."""
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'
    response = redirect(next_url)
    if check_for_language(lang_code):
        response.set_cookie(
            key=getattr(django_settings, 'LANGUAGE_COOKIE_NAME', 'django_language'),
            value=lang_code,
            max_age=getattr(django_settings, 'LANGUAGE_COOKIE_AGE', 60 * 60 * 24 * 365),
            path=getattr(django_settings, 'LANGUAGE_COOKIE_PATH', '/'),
            domain=getattr(django_settings, 'LANGUAGE_COOKIE_DOMAIN', None),
            secure=getattr(django_settings, 'LANGUAGE_COOKIE_SECURE', False),
            httponly=getattr(django_settings, 'LANGUAGE_COOKIE_HTTPONLY', False),
            samesite=getattr(django_settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax'),
        )
    return response


def _get_favorite_ids(request):
    # Возвращает множество id избранных товаров пользователя (или пустой set при ошибке/госте).
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
    # Подбирает корректный URL входа через Microsoft и возвращает строку URL.
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
    # Отображает страницу входа и возвращает HTML-ответ.
    return render(request, 'login.html')



def logout_view(request):
    # Выполняет выход по POST и возвращает redirect, иначе 400 Bad Request.
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return HttpResponseBadRequest()


def onboarding_view(request):
    # Показывает/завершает онбординг и возвращает HTML или redirect в зависимости от условий.
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
    # Главная: 4 последних товара или результаты поиска по q (навбар).
    q = (request.GET.get('q') or '').strip()

    qs = (
        Product.objects.filter(is_approved=True)
        .select_related('user', 'user__profile')
        .order_by('-created_at')
    )
    if request.user.is_authenticated:
        qs = qs.exclude(user=request.user)
    if q:
        q_lower = q.lower()
        product_list = list(qs)
        product_list = [
            p for p in product_list
            if q_lower in (p.title or '').lower() or q_lower in (p.description or '').lower()
        ]
        qs = product_list

    week_ago = timezone.now() - timezone.timedelta(days=7)
    weekly_new_count = sum(
        1 for p in qs
        if p.created_at and p.created_at >= week_ago
    )

    if not q:
        qs = qs[:4]

    return render(request, 'home.html', {
        'products': qs,
        'search_query': q,
        'favorite_ids': _get_favorite_ids(request),
        'weekly_new_count': weekly_new_count,
    })


def catalog_view(request):
    """Страница каталога с фильтрами, категориями и счётчиками по типу."""
    selected = request.GET.get('category')
    try:
        selected_id = int(selected) if selected else None
    except (ValueError, TypeError):
        selected_id = None

    product_type = request.GET.get('type', 'all')
    if product_type not in ('free', 'exchange', 'rental', 'all'):
        product_type = 'all'

    q = (request.GET.get('q') or '').strip()

    qs = (
        Product.objects.filter(is_approved=True)
        .select_related('user', 'user__profile')
        .order_by('-created_at')
    )
    if request.user.is_authenticated:
        qs = qs.exclude(user=request.user)
    if product_type != 'all':
        qs = qs.filter(type=product_type)
    if selected_id:
        qs = qs.filter(
            Q(main_category_id=selected_id) |
            Q(subcategory_id=selected_id) |
            Q(sub_subcategory_id=selected_id)
        )
    if q:
        q_lower = q.lower()
        product_list = list(qs)
        product_list = [
            p for p in product_list
            if q_lower in (p.title or '').lower() or q_lower in (p.description or '').lower()
        ]
        qs = product_list

    # Счётчики по типу для баннера
    all_approved = Product.objects.filter(is_approved=True)
    count_free = all_approved.filter(type='free').count()
    count_exchange = all_approved.filter(type='exchange').count()
    count_rental = all_approved.filter(type='rental').count()

    cats = Category.objects.filter(parent__isnull=True)
    return render(request, 'catalog.html', {
        'products': qs,
        'main_categories': cats,
        'selected_id': selected_id,
        'selected_type': product_type,
        'search_query': q,
        'favorite_ids': _get_favorite_ids(request),
        'count_free': count_free,
        'count_exchange': count_exchange,
        'count_rental': count_rental,
    })


@login_required
def my_ads(request):
    # Обрабатывает профиль пользователя (объявления/избранное), возвращает HTML, JSON или redirect.
    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        remove_fav = request.POST.get('remove_fav')
        upload_avatar = request.FILES.get('avatar')
        toggle_dark = request.POST.get('toggle_dark')
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1'

        if upload_avatar:
            profile = request.user.profile
            profile.avatar = upload_avatar
            profile.save(update_fields=['avatar'])
            if is_ajax:
                return JsonResponse({'ok': True, 'avatar_url': profile.avatar.url})
            return redirect('my_ads')
        elif toggle_dark is not None:
            profile = request.user.profile
            profile.dark_mode = not profile.dark_mode
            profile.save(update_fields=['dark_mode'])
            if is_ajax:
                return JsonResponse({'ok': True, 'dark_mode': profile.dark_mode})
            return redirect('my_ads')
        elif delete_id:
            product = get_object_or_404(Product, id=delete_id, user=request.user)
            product.delete()
            messages.success(request, "Объявление удалено.")
        elif remove_fav:
            try:
                pid = int(remove_fav)
                fav = Favorite.objects.filter(user=request.user, product_id=pid).first()
                if fav:
                    fav.delete()
                if is_ajax:
                    remaining = Favorite.objects.filter(user=request.user).count()
                    return JsonResponse({'ok': True, 'removed_id': pid, 'fav_count': remaining})
            except (ValueError, TypeError, OperationalError):
                if is_ajax:
                    return JsonResponse({'ok': False}, status=400)
        if is_ajax:
            return JsonResponse({'ok': True})
        return redirect('my_ads')

    selected_status = request.GET.get('status', 'all')
    if selected_status not in ('all', 'pending', 'active', 'rejected'):
        selected_status = 'all'

    own_products = Product.objects.filter(user=request.user).select_related('user', 'user__profile')
    if selected_status == 'pending':
        own_products = own_products.filter(is_approved=False)
    elif selected_status == 'active':
        own_products = own_products.filter(is_approved=True)
    elif selected_status == 'rejected':
        own_products = own_products.filter(status='rejected')

    favorites_available = True
    try:
        favorites_qs = (
            Favorite.objects.filter(user=request.user)
            .select_related('product', 'product__user', 'product__user__profile')
            .order_by('-created_at')
        )
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
        'selected_status': selected_status,
    })


@login_required
def edit_product(request, product_id):
    # Редактирует объявление текущего пользователя, обновляет данные/фото и возвращает HTML или redirect.
    product = get_object_or_404(Product, id=product_id, user=request.user)
    main_categories = Category.objects.filter(parent__isnull=True)
    if request.method == 'POST':
        post_data = request.POST.copy()
        raw_price = (post_data.get('price') or '').strip()
        if raw_price:
            post_data['price'] = ''.join(ch for ch in raw_price if ch.isdigit())

        form = ProductForm(post_data, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save(commit=False)
            updated_product.user = request.user

            exchange = request.POST.getlist('exchange_categories')
            if len(exchange) == 1 and ',' in exchange[0]:
                exchange = [item.strip() for item in exchange[0].split(',') if item.strip()]
            updated_product.exchange_categories = exchange

            if updated_product.type == 'free':
                updated_product.price = None

            if updated_product.type != 'exchange':
                updated_product.exchange_categories = []
                updated_product.exchange_other = ''

            if updated_product.type != 'rental':
                updated_product.price = None
                updated_product.rent_period = ''
                updated_product.min_rent_time = ''
                updated_product.return_rules = ''

            updated_product.save()

            # Update up to 5 photos: main + 4 extra.
            new_main = request.FILES.get('images_0')
            if new_main:
                updated_product.image = new_main
                updated_product.save(update_fields=['image'])

            existing_extra = list(updated_product.extra_images.order_by('order', 'id'))
            for i in range(1, 5):
                f = request.FILES.get(f'images_{i}')
                if not f:
                    continue
                extra_index = i - 1
                if extra_index < len(existing_extra):
                    extra = existing_extra[extra_index]
                    extra.image = f
                    extra.order = extra_index
                    extra.save(update_fields=['image', 'order'])
                else:
                    ProductImage.objects.create(product=updated_product, image=f, order=extra_index)

            messages.success(request, "Объявление обновлено.")
            return redirect('my_ads')
    else:
        form = ProductForm(instance=product)
    return render(request, 'edit_product.html', {
        'form': form,
        'product': product,
        'product_images': [product.image] + [img.image for img in product.extra_images_list() if img.image],
        'main_categories': main_categories,
    })


@login_required
def requests_view(request):
    # Управляет входящими/исходящими заявками (accept/reject/cancel и т.д.) и возвращает страницу заявок.
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
        elif decision == 'handover' and request.user == tr.owner and tr.status == 'accepted':
            tr.status = 'in_progress' if tr.action == 'rent' else 'completed'
            tr.save(update_fields=['status', 'updated_at'])
            if tr.action == 'rent':
                rental = RentItem.objects.filter(
                    product=tr.product,
                    renter=tr.requester,
                    owner=tr.owner,
                ).order_by('-created_at').first()
                if rental:
                    rental.status = 'rented'
                    rental.start_date = timezone.now()
                    rental.save(update_fields=['status', 'start_date', 'updated_at'])
        elif decision == 'mark_returned' and request.user == tr.owner and tr.status == 'in_progress' and tr.action == 'rent':
            tr.status = 'completed'
            tr.save(update_fields=['status', 'updated_at'])
            rental = RentItem.objects.filter(
                product=tr.product,
                renter=tr.requester,
                owner=tr.owner,
                status='rented',
            ).order_by('-created_at').first()
            if rental:
                rental.status = 'returned'
                rental.end_date = timezone.now()
                rental.save(update_fields=['status', 'end_date', 'updated_at'])

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'status': tr.status, 'action': tr.action})
        return redirect('requests')

    visible_statuses = ('pending', 'accepted', 'in_progress')
    incoming = list(
        TradeRequest.objects.filter(owner=request.user, status__in=visible_statuses)
        .select_related('product', 'requester')
        .order_by('-id')
    )
    outgoing = list(
        TradeRequest.objects.filter(requester=request.user, status__in=visible_statuses)
        .select_related('product', 'owner')
        .order_by('-id')
    )

    rent_requests = [r for r in (incoming + outgoing) if r.action == 'rent']
    rent_meta = {}
    if rent_requests:
        product_ids = {r.product_id for r in rent_requests}
        renter_ids = {r.requester_id for r in rent_requests}
        owner_ids = {r.owner_id for r in rent_requests}
        rent_items = RentItem.objects.filter(
            product_id__in=product_ids,
            renter_id__in=renter_ids,
            owner_id__in=owner_ids,
        ).order_by('-created_at')
        for item in rent_items:
            key = (item.product_id, item.renter_id, item.owner_id)
            if key not in rent_meta:
                rent_meta[key] = item
        for req in rent_requests:
            key = (req.product_id, req.requester_id, req.owner_id)
            setattr(req, 'rent_item', rent_meta.get(key))

    # Гарантированно показываем только что созданную заявку на аренду (из сессии)
    last_rent_id = request.session.pop('last_rent_request_id', None)
    if last_rent_id:
        try:
            tr = TradeRequest.objects.filter(id=last_rent_id, requester=request.user).select_related('product', 'owner').first()
            if tr and tr.status in visible_statuses and tr not in outgoing:
                outgoing = [tr] + [r for r in outgoing if r.id != tr.id]
        except Exception:
            pass

    history_statuses = ('completed', 'rejected', 'cancelled')
    history = list(
        TradeRequest.objects.filter(
            Q(owner=request.user) | Q(requester=request.user),
            status__in=history_statuses
        )
        .select_related('product', 'requester', 'owner')
        .order_by('-updated_at')[:50]
    )

    response = render(request, 'requests.html', {
        'incoming': incoming,
        'outgoing': outgoing,
        'history': history,
    })
    # Отключаем кэш, чтобы после редиректа с «Арендовать» всегда показывался актуальный список
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response


@login_required
def add_product(request):
    # Создает новое объявление, валидирует данные/фото и возвращает форму или redirect в профиль.
    main_categories = Category.objects.filter(parent__isnull=True)

    if request.method == 'POST':
        post_data = request.POST.copy()

        # На фронте цена может приходить отформатированной (например "2 000").
        raw_price = (post_data.get('price') or '').strip()
        if raw_price:
            post_data['price'] = ''.join(ch for ch in raw_price if ch.isdigit())

        form = ProductForm(post_data, request.FILES)

        if form.is_valid():

            #  Сбор фото
            files = []
            for i in range(5):
                f = request.FILES.get(f'images_{i}')
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

            #  Создание объекта
            p = form.save(commit=False)

            # Обмен может прийти как CSV из скрытого input или как список checkbox.
            exchange = request.POST.getlist('exchange_categories')
            if len(exchange) == 1 and ',' in exchange[0]:
                exchange = [item.strip() for item in exchange[0].split(',') if item.strip()]
            p.exchange_categories = exchange

           
            if p.type == 'free':
                p.price = None

            if p.type != 'exchange':
                p.exchange_categories = []
                p.exchange_other = ''

            if p.type != 'rental':
                p.price = None
                p.rent_period = ''
                p.min_rent_time = ''
                p.return_rules = ''

            #  пользователь
            p.user = request.user
            p.is_approved = False

            #  главное фото
            p.image = files[0]

            #  автоопределение
            inference = infer_product_from_image(files[0])

            if not (p.title or '').strip():
                p.title = (inference.title or '').strip()

            if not p.main_category and inference.main_category:
                p.main_category = inference.main_category
                p.subcategory = None
                p.sub_subcategory = None

            if not (p.title or '').strip():
                p.title = 'Предмет'

            #  дополнительные данные аренды (в описание)
            if p.type == 'rental':
                duration = request.POST.get('rent_period', '').strip()
                extra = []

                if duration:
                    extra.append(f'Период: {duration}')

                if p.min_rent_time:
                    extra.append(f'Мин. срок: {p.min_rent_time}')

                if extra:
                    p.description = (p.description or '').rstrip() + '\n\n' + '\n'.join(extra)

            #  Сохраняем
            p.save()

            #  дополнительные фото
            for i, f in enumerate(files[1:5]):
                ProductImage.objects.create(product=p, image=f, order=i)

            messages.info(request, "Ваше объявление отправлено на модерацию.")
            return redirect('my_ads')
        else:
            messages.error(request, "Не удалось опубликовать объявление. Проверьте обязательные поля.")

    else:
        form = ProductForm(initial={'type': 'free'})

    return render(request, 'add_product.html', {
        'form': form,
        'main_categories': main_categories
    })


@login_required
def infer_product_image(request):
    # Принимает фото, пытается определить товар/категорию и возвращает JSON с результатом.
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
    # Возвращает подкатегории для выбранной категории в формате JSON.
    subs = Category.objects.filter(parent_id=category_id)
    payload = [{'id': c.id, 'name': _(c.name)} for c in subs]
    return JsonResponse(payload, safe=False)


@login_required
def product_detail(request, product_id):
    # Показывает детальную страницу товара с галереей и состоянием отклика/избранного.
    product = get_object_or_404(Product, id=product_id)

    # Только автор может просматривать свой неободренный товар
    if not product.is_approved and product.user != request.user:
        messages.error(request, "Этот товар ещё не прошёл модерацию.")
        return redirect('home')

    try:
        in_favorites = Favorite.objects.filter(user=request.user, product=product).exists()
    except OperationalError:
        in_favorites = False
    has_existing_response = TradeRequest.objects.filter(
        product=product,
        requester=request.user
    ).exists()
    # Список всех фото: основное + доп. (для галереи без пустых слотов)
    product_images = []
    if product.image:
        product_images.append(product.image)
    for extra in product.extra_images_list():
        if getattr(extra, 'image', None):
            product_images.append(extra.image)

    # Убираем из описания служебные вставки вида:
    # "Период: week Мин. срок: Два дня" — и показываем их отдельными полями.
    display_description = (product.description or "").strip()
    display_rent_period = (product.rent_period or "").strip()
    display_min_rent_time = (product.min_rent_time or "").strip()

    if product.type == "rental" and display_description:
        period_match = re.search(r"Период:\s*([^\n\r]+?)(?=\s*Мин\.?\s*срок:|$)", display_description, flags=re.IGNORECASE)
        min_match = re.search(r"Мин\.?\s*срок:\s*([^\n\r]+)", display_description, flags=re.IGNORECASE)

        if period_match and not display_rent_period:
            display_rent_period = period_match.group(1).strip()
        if min_match and not display_min_rent_time:
            display_min_rent_time = min_match.group(1).strip()

        # Удаляем служебные куски из текста описания.
        display_description = re.sub(r"\s*Период:\s*[^\n\r]+?(?=\s*Мин\.?\s*срок:|$)", "", display_description, flags=re.IGNORECASE)
        display_description = re.sub(r"\s*Мин\.?\s*срок:\s*[^\n\r]+", "", display_description, flags=re.IGNORECASE)
        display_description = re.sub(r"\s{2,}", " ", display_description).strip()

    return render(request, 'product_detail.html', {
        'product': product,
        'in_favorites': in_favorites,
        'product_images': product_images,
        'display_description': display_description,
        'display_rent_period': display_rent_period,
        'display_min_rent_time': display_min_rent_time,
        'has_existing_response': has_existing_response,
    })


@login_required
def favorite_toggle(request, product_id):
    # Переключает товар в избранном и возвращает JSON (AJAX) или redirect (обычный запрос).
    """Добавить или убрать товар из избранного."""
    product = get_object_or_404(Product, id=product_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'

    if product.user == request.user:
        if is_ajax:
            return JsonResponse({'ok': False, 'error': 'own_product'}, status=400)
        messages.error(request, "Нельзя добавить в избранное свой товар.")
        return redirect('product_detail', product_id=product_id)

    try:
        fav, created = Favorite.objects.get_or_create(user=request.user, product=product)
        if not created:
            fav.delete()
            is_favorite = False
        else:
            is_favorite = True
    except OperationalError:
        if is_ajax:
            return JsonResponse({'ok': False, 'error': 'favorites_unavailable'}, status=503)
        messages.info(request, "Избранное пока недоступно.")
        is_favorite = None

    if is_ajax:
        return JsonResponse({
            'ok': True,
            'is_favorite': bool(is_favorite),
        })

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('product_detail', args=[product_id])
    return redirect(next_url)


@login_required
def product_action(request, product_id, action):
    # Создает заявку на товар (забрать/обмен/аренда), отправляет уведомление и возвращает redirect.
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
        action=action,
        desired_categories='',
        offered_item='',
    )
    if action == 'take':
        product.status = 'taken'
    else:
        product.status = 'exchanged'
    product.save()

    # Уведомление отправляем в фоне, чтобы не тормозить редирект пользователя.
    _notify_trade_request_async(product=product, requester=request.user, action=action)

    messages.success(request, "Заявка отправлена!")
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('requests')


@login_required
@require_http_methods(["POST"])
def push_subscribe(request):
    # Сохраняет push-подписку браузера пользователя и возвращает JSON со статусом.
    """Сохраняет push-подписку браузера."""
    try:
        data = json.loads(request.body)
        PushSubscription.objects.update_or_create(
            endpoint=data['endpoint'],
            defaults={
                'user': request.user,
                'p256dh': data['keys']['p256dh'],
                'auth': data['keys']['auth'],
            }
        )
        return JsonResponse({'ok': True})
    except Exception:
        return JsonResponse({'ok': False}, status=400)


@login_required
@require_http_methods(["POST"])
def push_unsubscribe(request):
    # Удаляет push-подписку браузера и возвращает JSON со статусом операции.
    """Удаляет push-подписку браузера."""
    try:
        data = json.loads(request.body)
        PushSubscription.objects.filter(endpoint=data['endpoint']).delete()
        return JsonResponse({'ok': True})
    except Exception:
        return JsonResponse({'ok': False}, status=400)


@login_required
def chat_list(request, chat_id=None):
    # Показывает список чатов и выбранный чат, помечает входящие как прочитанные, возвращает HTML.
    """Список всех чатов пользователя с деталями выбранного чата"""
    user_chats = Chat.objects.filter(participants=request.user).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time', '-updated_at')

    chats_with_info = []
    unread_total = 0
    for chat in user_chats:
        other_user = chat.get_other_participant(request.user)
        last_message = chat.messages.last()
        unread_count = chat.messages.filter(is_read=False).exclude(sender=request.user).count()

        chats_with_info.append({
            'chat': chat,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })
        unread_total += unread_count

    selected_chat = None
    selected_other_user = None
    selected_messages = []

    # Мобильная кнопка «Назад» в чате: /chat/?list=1 — только список, без автовыбора первого чата
    list_only = request.GET.get('list') == '1'

    if not list_only:
        chat_id = chat_id or request.GET.get('chat_id')
        if chat_id:
            try:
                selected_chat = Chat.objects.get(id=chat_id, participants=request.user)
                selected_other_user = selected_chat.get_other_participant(request.user)
                selected_chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
                selected_messages = selected_chat.messages.all()
            except (Chat.DoesNotExist, ValueError):
                pass
        elif chats_with_info:
            selected_chat = chats_with_info[0]['chat']
            selected_other_user = chats_with_info[0]['other_user']
            selected_chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
            selected_messages = selected_chat.messages.all()

    return render(request, 'chat/index.html', {
        'chats': chats_with_info,
        'unread_total': unread_total,
        'selected_chat': selected_chat,
        'selected_other_user': selected_other_user,
        'selected_messages': selected_messages,
    })


@login_required
def chat_detail(request, chat_id):
    # Открывает конкретный чат, отмечает сообщения как прочитанные и возвращает страницу чата.
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    other_user = chat.get_other_participant(request.user)
    chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    messages_list = chat.messages.all()
    return render(request, 'chat/detail.html', {
        'chat': chat,
        'other_user': other_user,
        'messages': messages_list,
    })


@login_required
@require_http_methods(["POST"])
def send_message(request, chat_id):
    # Отправляет сообщение/изображение в чат и возвращает redirect обратно к списку чатов.
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    text = request.POST.get('text', '').strip()
    image = request.FILES.get('image')

    if not text and not image:
        messages.error(request, "Сообщение не может быть пустым")
        return redirect(f'{reverse("chat_list")}?chat_id={chat_id}')

    Message.objects.create(
        chat=chat,
        sender=request.user,
        text=text if text else '',
        image=image if image else None
    )

    chat.save()
    if text:
        notify_new_message(chat, request.user, text)

    return redirect(f'{reverse("chat_list")}?chat_id={chat_id}')


@login_required
def get_messages(request, chat_id):
    # Возвращает сообщения выбранного чата в JSON и помечает входящие как прочитанные.
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    messages_list = chat.messages.all()
    chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    messages_data = [{
        'id': msg.id,
        'sender': msg.sender.username,
        'text': msg.text,
        'image': msg.image.url if msg.image else None,
        'is_read': msg.is_read,
        'created_at': msg.created_at.isoformat(),
        'is_own': msg.sender == request.user,
    } for msg in messages_list]

    return JsonResponse({
        'messages': messages_data,
        'chat_id': chat_id,
    })


@login_required
@require_http_methods(["POST"])
def delete_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    chat.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect(f'{reverse("chat_list")}?list=1')


@login_required
def start_chat(request, user_id):
    # Создает новый чат или открывает существующий и возвращает redirect на чат.
    other_user = get_object_or_404(User, id=user_id)

    if other_user == request.user:
        messages.error(request, "Нельзя начать чат с самим собой")
        return redirect('home')

    product_id = request.GET.get('product_id')
    product = None
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            pass

    if product:
        existing_chat = Chat.objects.filter(
            participants=request.user,
            product=product
        ).filter(
            participants=other_user
        ).distinct().first()
    else:
        existing_chat = Chat.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).distinct().first()

    if existing_chat:
        return redirect(f'{reverse("chat_list")}?chat_id={existing_chat.id}')

    new_chat = Chat.objects.create(product=product)
    new_chat.participants.add(request.user, other_user)

    return redirect(f'{reverse("chat_list")}?chat_id={new_chat.id}')


@login_required
def rentals_list(request):
    # Формирует список доступных аренд и возвращает HTML или JSON по запросу.
    selected = request.GET.get('category')
    try:
        selected_id = int(selected) if selected else None
    except (TypeError, ValueError):
        selected_id = None

    available_products = Product.objects.filter(
        type='rental',
        status='available',
        is_approved=True
    ).exclude(user=request.user)

    rented_product_ids = RentItem.objects.filter(
        status='rented'
    ).values_list('product_id', flat=True)

    available_products = available_products.exclude(id__in=rented_product_ids)

    if selected_id:
        available_products = available_products.filter(
            Q(main_category_id=selected_id) |
            Q(subcategory_id=selected_id) |
            Q(sub_subcategory_id=selected_id)
        )

    categories = Category.objects.filter(parent__isnull=True).prefetch_related('category_set')

    open_category_id = None
    if selected_id:
        for cat in categories:
            if cat.id == selected_id:
                open_category_id = cat.id
                break
            for child in cat.category_set.all():
                if child.id == selected_id:
                    open_category_id = cat.id
                    break
            if open_category_id:
                break

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        products_data = [{
            'id': product.id,
            'title': product.title,
            'description': product.description,
            'image': product.image.url if product.image else None,
            'owner': {
                'id': product.user.id,
                'username': product.user.username,
            },
            'phone': product.phone,
            'created_at': product.created_at.isoformat(),
        } for product in available_products]

        return JsonResponse({'products': products_data})

    favorite_ids = set()
    try:
        favorite_ids = set(
            Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    except OperationalError:
        pass

    return render(request, 'rentals/index.html', {
        'products': available_products,
        'categories': categories,
        'selected_id': selected_id,
        'open_category_id': open_category_id,
        'favorite_ids': favorite_ids,
    })




@login_required
def rental_detail(request, rental_id):
    # Возвращает детальную информацию по аренде (HTML/JSON) с проверкой прав доступа.
    rental = get_object_or_404(RentItem, id=rental_id)

    if rental.renter != request.user and rental.owner != request.user:
        messages.error(request, "У вас нет доступа к этой аренде")
        return redirect('rentals_list')

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': rental.id,
            'product': {
                'id': rental.product.id,
                'title': rental.product.title,
                'description': rental.product.description,
                'image': rental.product.image.url if rental.product.image else None,
            },
            'renter': {
                'id': rental.renter.id,
                'username': rental.renter.username,
            },
            'owner': {
                'id': rental.owner.id,
                'username': rental.owner.username,
            },
            'status': rental.status,
            'status_display': rental.get_status_display(),
            'start_date': rental.start_date.isoformat(),
            'end_date': rental.end_date.isoformat() if rental.end_date else None,
            'expected_return_date': rental.expected_return_date.isoformat() if rental.expected_return_date else None,
            'created_at': rental.created_at.isoformat(),
            'updated_at': rental.updated_at.isoformat(),
        })

    return render(request, 'rentals/detail.html', {
        'rental': rental,
        'is_renter': rental.renter == request.user,
        'is_owner': rental.owner == request.user,
    })


@login_required
def create_rental(request):
    # Создает заявку/запись аренды, обновляет статус товара и возвращает JSON или redirect.
    if request.method != 'POST':
        messages.info(request, "Откройте карточку товара и нажмите «Арендовать» для отправки заявки.")
        return redirect(reverse('requests'))

    product_id = request.POST.get('product_id')
    expected_return_date = request.POST.get('expected_return_date')

    if not product_id:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'product_id is required'}, status=400)
        messages.info(request, "Откройте карточку товара и нажмите «Арендовать» для отправки заявки.")
        return redirect(reverse('requests'))

    product = get_object_or_404(Product, id=product_id)

    if product.user == request.user:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'Cannot rent your own product'}, status=400)
        messages.error(request, "Нельзя арендовать свой товар")
        return redirect('product_detail', product_id=product_id)

    existing_rental = RentItem.objects.filter(
        product=product,
        renter=request.user,
        status='rented'
    ).first()

    if existing_rental:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'Active rental already exists'}, status=400)
        messages.error(request, "У вас уже есть активная аренда этого товара")
        return redirect(reverse('requests'))

    with transaction.atomic():
        tr = TradeRequest.objects.filter(
            product=product,
            requester=request.user,
            owner=product.user,
            action='rent',
        ).first()
        if tr:
            if tr.status in ('rejected', 'cancelled'):
                tr.status = 'pending'
                tr.save()
        else:
            tr = TradeRequest.objects.create(
                product=product,
                requester=request.user,
                owner=product.user,
                action='rent',
                status='pending',
                desired_categories='',
                offered_item='',
            )

    request.session['last_rent_request_id'] = tr.id

    try:
        with transaction.atomic():
            rental = RentItem.objects.create(
                product=product,
                renter=request.user,
                owner=product.user,
                expected_return_date=expected_return_date if expected_return_date else None,
            )
            product.status = 'taken'
            product.save(update_fields=['status'])
    except Exception:
        messages.info(request, "Заявка на аренду добавлена в список. Проверьте раздел «Исходящие заявки».")
        return redirect(reverse('requests'))

    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'id': rental.id,
            'message': 'Rental created successfully',
        }, status=201)

    notify_trade_request(product=product, requester=request.user, action='rent')

    messages.success(request, "Заявка на аренду отправлена!")
    return redirect(reverse('requests'))


@login_required
@require_http_methods(["POST", "PATCH"])
def update_rental(request, rental_id):
    # Обновляет статус аренды по POST/PATCH и возвращает JSON или redirect с результатом.
    rental = get_object_or_404(RentItem, id=rental_id)

    if rental.renter != request.user and rental.owner != request.user:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'Access denied'}, status=403)
        messages.error(request, "У вас нет доступа к этой аренде")
        return redirect('rentals_list')

    if request.method == 'POST':
        new_status = request.POST.get('status')
    else:
        data = json.loads(request.body)
        new_status = data.get('status')

    if not new_status:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'status is required'}, status=400)
        messages.error(request, "Не указан статус")
        return redirect('rental_detail', rental_id=rental_id)

    rental.status = new_status
    if new_status == 'returned' and not rental.end_date:
        rental.end_date = timezone.now()

    rental.save()

    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'id': rental.id,
            'status': rental.status,
            'status_display': rental.get_status_display(),
            'message': 'Rental updated successfully',
        })

    messages.success(request, f"Статус аренды изменен на '{rental.get_status_display()}'")
    return redirect('rental_detail', rental_id=rental_id)
