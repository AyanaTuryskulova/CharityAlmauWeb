# core/views.py

import logging
import json
import re
import threading

from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q, Max
from django.db.utils import OperationalError
from django.urls import reverse, NoReverseMatch
from django.utils.translation import check_for_language
from django.utils.translation import gettext as _
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_GET
from django.conf import settings as django_settings

from .models import Category, Product, ProductImage, TradeRequest, Favorite, Chat, Message, PushSubscription
from .forms import ProductForm
from .services.image_autofill import infer_product_from_image
from .notifications import notify_trade_request
from .email_utils import notify_new_message


def _notify_trade_request_async(product, requester, action):
    # Р—Р°РїСѓСЃРєР°РµС‚ РѕС‚РїСЂР°РІРєСѓ СѓРІРµРґРѕРјР»РµРЅРёСЏ Рѕ Р·Р°СЏРІРєРµ РІ РѕС‚РґРµР»СЊРЅРѕРј РїРѕС‚РѕРєРµ Рё РЅРёС‡РµРіРѕ РЅРµ РІРѕР·РІСЂР°С‰Р°РµС‚.
    """Sends trade-request notifications in background to avoid blocking redirect."""
    def _run():
        try:
            notify_trade_request(product=product, requester=requester, action=action)
        except Exception:
            logger = logging.getLogger(__name__)
            logger.exception("Failed to send trade request notification")

    threading.Thread(target=_run, daemon=True).start()


def switch_language(request, lang_code):
    # РџРµСЂРµРєР»СЋС‡Р°РµС‚ СЏР·С‹Рє РёРЅС‚РµСЂС„РµР№СЃР° С‡РµСЂРµР· cookie Рё РІРѕР·РІСЂР°С‰Р°РµС‚ redirect РЅР° РїСЂРµРґС‹РґСѓС‰СѓСЋ СЃС‚СЂР°РЅРёС†Сѓ.
    """РџРµСЂРµРєР»СЋС‡Р°РµС‚ СЏР·С‹Рє РёРЅС‚РµСЂС„РµР№СЃР° С‡РµСЂРµР· cookie Рё РїРµСЂРµРЅР°РїСЂР°РІР»СЏРµС‚ РѕР±СЂР°С‚РЅРѕ."""
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
    # Р’РѕР·РІСЂР°С‰Р°РµС‚ РјРЅРѕР¶РµСЃС‚РІРѕ id РёР·Р±СЂР°РЅРЅС‹С… С‚РѕРІР°СЂРѕРІ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ (РёР»Рё РїСѓСЃС‚РѕР№ set РїСЂРё РѕС€РёР±РєРµ/РіРѕСЃС‚Рµ).
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ set id С‚РѕРІР°СЂРѕРІ, РЅР°С…РѕРґСЏС‰РёС…СЃСЏ РІ РёР·Р±СЂР°РЅРЅРѕРј Сѓ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ."""
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return set()
    try:
        return set(
            Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    except OperationalError:
        return set()


def _ms_login_url():
    # РџРѕРґР±РёСЂР°РµС‚ РєРѕСЂСЂРµРєС‚РЅС‹Р№ URL РІС…РѕРґР° С‡РµСЂРµР· Microsoft Рё РІРѕР·РІСЂР°С‰Р°РµС‚ СЃС‚СЂРѕРєСѓ URL.
    # 1) РїСЂРѕР±СѓРµРј РїСЂРѕРІР°Р№РґРµСЂ-СЃРїРµС†РёС„РёС‡РЅРѕРµ РёРјСЏ
    try:
        return reverse('microsoft_login')
    except NoReverseMatch:
        pass
    # 2) РїСЂРѕР±СѓРµРј РѕР±С‰РµРµ РёРјСЏ СЃС‚Р°СЂС‹С… РІРµСЂСЃРёР№
    try:
        return reverse('socialaccount_login', kwargs={'provider': 'microsoft'})
    except NoReverseMatch:
        pass
    # 3) РїРѕСЃР»РµРґРЅРёР№ РЅР°РґС‘Р¶РЅС‹Р№ РІР°СЂРёР°РЅС‚ вЂ” РїСЂСЏРјРѕР№ РїСѓС‚СЊ
    return '/accounts/microsoft/login/'


def login_view(request):
    # РћС‚РѕР±СЂР°Р¶Р°РµС‚ СЃС‚СЂР°РЅРёС†Сѓ РІС…РѕРґР° Рё РІРѕР·РІСЂР°С‰Р°РµС‚ HTML-РѕС‚РІРµС‚.
    return render(request, 'login.html')



def logout_view(request):
    # Р’С‹РїРѕР»РЅСЏРµС‚ РІС‹С…РѕРґ РїРѕ POST Рё РІРѕР·РІСЂР°С‰Р°РµС‚ redirect, РёРЅР°С‡Рµ 400 Bad Request.
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return HttpResponseBadRequest()


def onboarding_view(request):
    # РџРѕРєР°Р·С‹РІР°РµС‚/Р·Р°РІРµСЂС€Р°РµС‚ РѕРЅР±РѕСЂРґРёРЅРі Рё РІРѕР·РІСЂР°С‰Р°РµС‚ HTML РёР»Рё redirect РІ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё РѕС‚ СѓСЃР»РѕРІРёР№.
    # Р•СЃР»Рё РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ Р°СѓС‚РµРЅС‚РёС„РёС†РёСЂРѕРІР°РЅ Рё СѓР¶Рµ РїСЂРѕС€С‘Р» РѕРЅР±РѕСЂРґРёРЅРі,
    # РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ РїРµСЂРµРЅР°РїСЂР°РІР»СЏРµРј РЅР° РґРѕРјР°С€РЅСЋСЋ СЃС‚СЂР°РЅРёС†Сѓ.
    # РќРѕ РµСЃР»Рё РІ GET РїРµСЂРµРґР°РЅ РїР°СЂР°РјРµС‚СЂ force=1, РїРѕРєР°Р·С‹РІР°РµРј РѕРЅР±РѕСЂРґРёРЅРі РІ Р»СЋР±РѕРј СЃР»СѓС‡Р°Рµ.
    force = request.GET.get('force')
    if request.user.is_authenticated and not force and request.session.get('onboarded', False):
        return redirect('home')

    if request.method == 'POST':
        # РћС‚РјРµС‡Р°РµРј РІ СЃРµСЃСЃРёРё, С‡С‚Рѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ РїСЂРѕС€С‘Р» РѕРЅР±РѕСЂРґРёРЅРі
        request.session['onboarded'] = True
        return redirect('home')

    return render(request, 'onboarding.html')


HOME_FEED_PAGE_SIZE = 4


def _home_products_queryset(request, q=''):
    qs = (
        Product.objects.filter(is_approved=True)
        .select_related('user', 'user__profile', 'main_category')
        .order_by('-created_at')
    )
    if request.user.is_authenticated:
        qs = qs.exclude(user=request.user)
    q = (q or '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    return qs


def home_view(request):
    q = (request.GET.get('q') or '').strip()
    qs = _home_products_queryset(request, q)
    total_count = qs.count()
    products = list(qs[:HOME_FEED_PAGE_SIZE])
    week_ago = timezone.now() - timezone.timedelta(days=7)
    weekly_new_count = qs.filter(created_at__gte=week_ago).count()

    return render(request, 'home.html', {
        'products': products,
        'search_query': q,
        'favorite_ids': _get_favorite_ids(request),
        'weekly_new_count': weekly_new_count,
        'has_more': total_count > len(products),
        'next_offset': len(products),
        'feed_page_size': HOME_FEED_PAGE_SIZE,
    })


@require_GET
def home_feed(request):
    try:
        offset = max(0, int(request.GET.get('offset', 0)))
    except (TypeError, ValueError):
        offset = 0
    try:
        limit = min(max(1, int(request.GET.get('limit', HOME_FEED_PAGE_SIZE))), 12)
    except (TypeError, ValueError):
        limit = HOME_FEED_PAGE_SIZE

    q = (request.GET.get('q') or '').strip()
    qs = _home_products_queryset(request, q)
    total_count = qs.count()
    products = list(qs[offset:offset + limit])
    next_offset = offset + len(products)

    if products:
        html = render_to_string(
            'includes/home_product_card.html',
            {
                'products': products,
                'favorite_ids': _get_favorite_ids(request),
                'request': request,
            },
            request=request,
        )
    elif offset == 0:
        html = render_to_string(
            'includes/home_empty_feed.html',
            {'search_query': q},
            request=request,
        )
    else:
        html = ''

    if q:
        feed_title = _('Результаты по запросу «%(query)s»') % {'query': q}
    else:
        feed_title = _('Добавлено недавно')

    return JsonResponse({
        'html': html,
        'has_more': next_offset < total_count,
        'next_offset': next_offset,
        'feed_title': feed_title,
        'search_query': q,
    })


CATALOG_PAGE_SIZE = 8


def catalog_view(request):
    """Страница каталога с фильтрами, категориями и подгрузкой по 8 через ?offset=."""
    selected = request.GET.get('category')
    try:
        selected_id = int(selected) if selected else None
    except (ValueError, TypeError):
        selected_id = None

    product_type = request.GET.get('type', 'all')
    if product_type not in ('free', 'exchange', 'rental', 'all'):
        product_type = 'all'

    q = (request.GET.get('q') or '').strip()
    sort = request.GET.get('sort', 'new')
    if sort not in ('new', 'old'):
        sort = 'new'

    try:
        shown = max(0, int(request.GET.get('offset', 0)))
    except (TypeError, ValueError):
        shown = 0

    qs = (
        Product.objects.filter(is_approved=True)
        .select_related('user', 'user__profile', 'main_category')
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
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if sort == 'old':
        qs = qs.order_by('created_at')
    else:
        qs = qs.order_by('-created_at')

    total_count = qs.count()
    products = list(qs[:shown + CATALOG_PAGE_SIZE])
    has_more = total_count > len(products)
    load_more_url = None
    if has_more:
        params = request.GET.copy()
        params['offset'] = str(len(products))
        load_more_url = '?' + params.urlencode()

    all_approved = Product.objects.filter(is_approved=True)
    count_free = all_approved.filter(type='free').count()
    count_exchange = all_approved.filter(type='exchange').count()
    count_rental = all_approved.filter(type='rental').count()

    cats = Category.objects.filter(parent__isnull=True)
    return render(request, 'catalog.html', {
        'products': products,
        'main_categories': cats,
        'selected_id': selected_id,
        'selected_type': product_type,
        'search_query': q,
        'sort': sort,
        'favorite_ids': _get_favorite_ids(request),
        'count_free': count_free,
        'count_exchange': count_exchange,
        'count_rental': count_rental,
        'has_more': has_more,
        'load_more_url': load_more_url,
    })


@login_required
def my_ads(request):
    # РћР±СЂР°Р±Р°С‚С‹РІР°РµС‚ РїСЂРѕС„РёР»СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ (РѕР±СЉСЏРІР»РµРЅРёСЏ/РёР·Р±СЂР°РЅРЅРѕРµ), РІРѕР·РІСЂР°С‰Р°РµС‚ HTML, JSON РёР»Рё redirect.
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
            messages.success(request, "РћР±СЉСЏРІР»РµРЅРёРµ СѓРґР°Р»РµРЅРѕ.")
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
    # Р РµРґР°РєС‚РёСЂСѓРµС‚ РѕР±СЉСЏРІР»РµРЅРёРµ С‚РµРєСѓС‰РµРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ, РѕР±РЅРѕРІР»СЏРµС‚ РґР°РЅРЅС‹Рµ/С„РѕС‚Рѕ Рё РІРѕР·РІСЂР°С‰Р°РµС‚ HTML РёР»Рё redirect.
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

            messages.success(request, "РћР±СЉСЏРІР»РµРЅРёРµ РѕР±РЅРѕРІР»РµРЅРѕ.")
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
    # РЈРїСЂР°РІР»СЏРµС‚ РІС…РѕРґСЏС‰РёРјРё/РёСЃС…РѕРґСЏС‰РёРјРё Р·Р°СЏРІРєР°РјРё (accept/reject/cancel Рё С‚.Рґ.) Рё РІРѕР·РІСЂР°С‰Р°РµС‚ СЃС‚СЂР°РЅРёС†Сѓ Р·Р°СЏРІРѕРє.
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
        elif decision == 'mark_returned' and request.user == tr.owner and tr.status == 'in_progress' and tr.action == 'rent':
            tr.status = 'completed'
            tr.save(update_fields=['status', 'updated_at'])

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
    # РћС‚РєР»СЋС‡Р°РµРј РєСЌС€, С‡С‚РѕР±С‹ РїРѕСЃР»Рµ СЂРµРґРёСЂРµРєС‚Р° СЃ В«РђСЂРµРЅРґРѕРІР°С‚СЊВ» РІСЃРµРіРґР° РїРѕРєР°Р·С‹РІР°Р»СЃСЏ Р°РєС‚СѓР°Р»СЊРЅС‹Р№ СЃРїРёСЃРѕРє
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response


@login_required
def add_product(request):
    # РЎРѕР·РґР°РµС‚ РЅРѕРІРѕРµ РѕР±СЉСЏРІР»РµРЅРёРµ, РІР°Р»РёРґРёСЂСѓРµС‚ РґР°РЅРЅС‹Рµ/С„РѕС‚Рѕ Рё РІРѕР·РІСЂР°С‰Р°РµС‚ С„РѕСЂРјСѓ РёР»Рё redirect РІ РїСЂРѕС„РёР»СЊ.
    main_categories = Category.objects.filter(parent__isnull=True)

    if request.method == 'POST':
        post_data = request.POST.copy()

        # РќР° С„СЂРѕРЅС‚Рµ С†РµРЅР° РјРѕР¶РµС‚ РїСЂРёС…РѕРґРёС‚СЊ РѕС‚С„РѕСЂРјР°С‚РёСЂРѕРІР°РЅРЅРѕР№ (РЅР°РїСЂРёРјРµСЂ "2 000").
        raw_price = (post_data.get('price') or '').strip()
        if raw_price:
            post_data['price'] = ''.join(ch for ch in raw_price if ch.isdigit())

        form = ProductForm(post_data, request.FILES)

        if form.is_valid():

            #  РЎР±РѕСЂ С„РѕС‚Рѕ
            files = []
            for i in range(5):
                f = request.FILES.get(f'images_{i}')
                if f:
                    files.append(f)

            if not files:
                form.add_error(None, 'Р”РѕР±Р°РІСЊС‚Рµ С…РѕС‚СЏ Р±С‹ РѕРґРЅРѕ С„РѕС‚Рѕ.')
                return render(request, 'add_product.html', {
                    'form': form,
                    'main_categories': main_categories,
                })

            if len(files) > 5:
                form.add_error(None, 'РњРѕР¶РЅРѕ Р·Р°РіСЂСѓР·РёС‚СЊ РЅРµ Р±РѕР»РµРµ 5 С„РѕС‚Рѕ.')
                return render(request, 'add_product.html', {
                    'form': form,
                    'main_categories': main_categories,
                })

            #  РЎРѕР·РґР°РЅРёРµ РѕР±СЉРµРєС‚Р°
            p = form.save(commit=False)

            # РћР±РјРµРЅ РјРѕР¶РµС‚ РїСЂРёР№С‚Рё РєР°Рє CSV РёР· СЃРєСЂС‹С‚РѕРіРѕ input РёР»Рё РєР°Рє СЃРїРёСЃРѕРє checkbox.
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

            #  РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ
            p.user = request.user
            p.is_approved = False

            #  РіР»Р°РІРЅРѕРµ С„РѕС‚Рѕ
            p.image = files[0]

            #  Р°РІС‚РѕРѕРїСЂРµРґРµР»РµРЅРёРµ
            inference = infer_product_from_image(files[0])

            if not (p.title or '').strip():
                p.title = (inference.title or '').strip()

            if not p.main_category and inference.main_category:
                p.main_category = inference.main_category
                p.subcategory = None
                p.sub_subcategory = None

            if not (p.title or '').strip():
                p.title = 'РџСЂРµРґРјРµС‚'

            #  РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ РґР°РЅРЅС‹Рµ Р°СЂРµРЅРґС‹ (РІ РѕРїРёСЃР°РЅРёРµ)
            if p.type == 'rental':
                duration = request.POST.get('rent_period', '').strip()
                extra = []

                if duration:
                    extra.append(f'РџРµСЂРёРѕРґ: {duration}')

                if p.min_rent_time:
                    extra.append(f'РњРёРЅ. СЃСЂРѕРє: {p.min_rent_time}')

                if extra:
                    p.description = (p.description or '').rstrip() + '\n\n' + '\n'.join(extra)

            #  РЎРѕС…СЂР°РЅСЏРµРј
            p.save()

            #  РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ С„РѕС‚Рѕ
            for i, f in enumerate(files[1:5]):
                ProductImage.objects.create(product=p, image=f, order=i)

            messages.info(request, "Р’Р°С€Рµ РѕР±СЉСЏРІР»РµРЅРёРµ РѕС‚РїСЂР°РІР»РµРЅРѕ РЅР° РјРѕРґРµСЂР°С†РёСЋ.")
            return redirect('my_ads')
        else:
            messages.error(request, "РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСѓР±Р»РёРєРѕРІР°С‚СЊ РѕР±СЉСЏРІР»РµРЅРёРµ. РџСЂРѕРІРµСЂСЊС‚Рµ РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ РїРѕР»СЏ.")

    else:
        form = ProductForm(initial={'type': 'free'})

    return render(request, 'add_product.html', {
        'form': form,
        'main_categories': main_categories
    })


@login_required
def infer_product_image(request):
    # РџСЂРёРЅРёРјР°РµС‚ С„РѕС‚Рѕ, РїС‹С‚Р°РµС‚СЃСЏ РѕРїСЂРµРґРµР»РёС‚СЊ С‚РѕРІР°СЂ/РєР°С‚РµРіРѕСЂРёСЋ Рё РІРѕР·РІСЂР°С‰Р°РµС‚ JSON СЃ СЂРµР·СѓР»СЊС‚Р°С‚РѕРј.
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
    # Р’РѕР·РІСЂР°С‰Р°РµС‚ РїРѕРґРєР°С‚РµРіРѕСЂРёРё РґР»СЏ РІС‹Р±СЂР°РЅРЅРѕР№ РєР°С‚РµРіРѕСЂРёРё РІ С„РѕСЂРјР°С‚Рµ JSON.
    subs = Category.objects.filter(parent_id=category_id)
    payload = [{'id': c.id, 'name': _(c.name)} for c in subs]
    return JsonResponse(payload, safe=False)


@login_required
def product_detail(request, product_id):
    # РџРѕРєР°Р·С‹РІР°РµС‚ РґРµС‚Р°Р»СЊРЅСѓСЋ СЃС‚СЂР°РЅРёС†Сѓ С‚РѕРІР°СЂР° СЃ РіР°Р»РµСЂРµРµР№ Рё СЃРѕСЃС‚РѕСЏРЅРёРµРј РѕС‚РєР»РёРєР°/РёР·Р±СЂР°РЅРЅРѕРіРѕ.
    product = get_object_or_404(Product, id=product_id)

    # РўРѕР»СЊРєРѕ Р°РІС‚РѕСЂ РјРѕР¶РµС‚ РїСЂРѕСЃРјР°С‚СЂРёРІР°С‚СЊ СЃРІРѕР№ РЅРµРѕР±РѕРґСЂРµРЅРЅС‹Р№ С‚РѕРІР°СЂ
    if not product.is_approved and product.user != request.user:
        messages.error(request, "Р­С‚РѕС‚ С‚РѕРІР°СЂ РµС‰С‘ РЅРµ РїСЂРѕС€С‘Р» РјРѕРґРµСЂР°С†РёСЋ.")
        return redirect('home')

    try:
        in_favorites = Favorite.objects.filter(user=request.user, product=product).exists()
    except OperationalError:
        in_favorites = False
    has_existing_response = TradeRequest.objects.filter(
        product=product,
        requester=request.user
    ).exists()
    # РЎРїРёСЃРѕРє РІСЃРµС… С„РѕС‚Рѕ: РѕСЃРЅРѕРІРЅРѕРµ + РґРѕРї. (РґР»СЏ РіР°Р»РµСЂРµРё Р±РµР· РїСѓСЃС‚С‹С… СЃР»РѕС‚РѕРІ)
    product_images = []
    if product.image:
        product_images.append(product.image)
    for extra in product.extra_images_list():
        if getattr(extra, 'image', None):
            product_images.append(extra.image)

    # РЈР±РёСЂР°РµРј РёР· РѕРїРёСЃР°РЅРёСЏ СЃР»СѓР¶РµР±РЅС‹Рµ РІСЃС‚Р°РІРєРё РІРёРґР°:
    # "РџРµСЂРёРѕРґ: week РњРёРЅ. СЃСЂРѕРє: Р”РІР° РґРЅСЏ" вЂ” Рё РїРѕРєР°Р·С‹РІР°РµРј РёС… РѕС‚РґРµР»СЊРЅС‹РјРё РїРѕР»СЏРјРё.
    display_description = (product.description or "").strip()
    display_rent_period = (product.rent_period or "").strip()
    display_min_rent_time = (product.min_rent_time or "").strip()

    if product.type == "rental" and display_description:
        period_match = re.search(r"РџРµСЂРёРѕРґ:\s*([^\n\r]+?)(?=\s*РњРёРЅ\.?\s*СЃСЂРѕРє:|$)", display_description, flags=re.IGNORECASE)
        min_match = re.search(r"РњРёРЅ\.?\s*СЃСЂРѕРє:\s*([^\n\r]+)", display_description, flags=re.IGNORECASE)

        if period_match and not display_rent_period:
            display_rent_period = period_match.group(1).strip()
        if min_match and not display_min_rent_time:
            display_min_rent_time = min_match.group(1).strip()

        # РЈРґР°Р»СЏРµРј СЃР»СѓР¶РµР±РЅС‹Рµ РєСѓСЃРєРё РёР· С‚РµРєСЃС‚Р° РѕРїРёСЃР°РЅРёСЏ.
        display_description = re.sub(r"\s*РџРµСЂРёРѕРґ:\s*[^\n\r]+?(?=\s*РњРёРЅ\.?\s*СЃСЂРѕРє:|$)", "", display_description, flags=re.IGNORECASE)
        display_description = re.sub(r"\s*РњРёРЅ\.?\s*СЃСЂРѕРє:\s*[^\n\r]+", "", display_description, flags=re.IGNORECASE)
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
    # РџРµСЂРµРєР»СЋС‡Р°РµС‚ С‚РѕРІР°СЂ РІ РёР·Р±СЂР°РЅРЅРѕРј Рё РІРѕР·РІСЂР°С‰Р°РµС‚ JSON (AJAX) РёР»Рё redirect (РѕР±С‹С‡РЅС‹Р№ Р·Р°РїСЂРѕСЃ).
    """Р”РѕР±Р°РІРёС‚СЊ РёР»Рё СѓР±СЂР°С‚СЊ С‚РѕРІР°СЂ РёР· РёР·Р±СЂР°РЅРЅРѕРіРѕ."""
    product = get_object_or_404(Product, id=product_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'

    if product.user == request.user:
        if is_ajax:
            return JsonResponse({'ok': False, 'error': 'own_product'}, status=400)
        messages.error(request, "РќРµР»СЊР·СЏ РґРѕР±Р°РІРёС‚СЊ РІ РёР·Р±СЂР°РЅРЅРѕРµ СЃРІРѕР№ С‚РѕРІР°СЂ.")
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
        messages.info(request, "РР·Р±СЂР°РЅРЅРѕРµ РїРѕРєР° РЅРµРґРѕСЃС‚СѓРїРЅРѕ.")
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
    # РЎРѕР·РґР°РµС‚ Р·Р°СЏРІРєСѓ РЅР° С‚РѕРІР°СЂ (Р·Р°Р±СЂР°С‚СЊ/РѕР±РјРµРЅ/Р°СЂРµРЅРґР°), РѕС‚РїСЂР°РІР»СЏРµС‚ СѓРІРµРґРѕРјР»РµРЅРёРµ Рё РІРѕР·РІСЂР°С‰Р°РµС‚ redirect.
    product = get_object_or_404(Product, id=product_id)

    if product.user == request.user:
        messages.error(request, "РќРµР»СЊР·СЏ Р·Р°РїСЂРѕСЃРёС‚СЊ СЃРІРѕР№ Р¶Рµ С‚РѕРІР°СЂ.")
        return redirect('home')

    if not product.is_approved:
        messages.error(request, "Р­С‚РѕС‚ С‚РѕРІР°СЂ РµС‰С‘ РЅРµ РѕРґРѕР±СЂРµРЅ.")
        return redirect('home')

    tr = TradeRequest.objects.create(
        product=product,
        requester=request.user,
        owner=product.user,
        action=action,
        desired_categories='',
        offered_item='',
    )
    if action in ('take', 'rent'):
        product.status = 'taken'
    elif action == 'exchange':
        product.status = 'exchanged'
    product.save()

    # РЈРІРµРґРѕРјР»РµРЅРёРµ РѕС‚РїСЂР°РІР»СЏРµРј РІ С„РѕРЅРµ, С‡С‚РѕР±С‹ РЅРµ С‚РѕСЂРјРѕР·РёС‚СЊ СЂРµРґРёСЂРµРєС‚ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ.
    _notify_trade_request_async(product=product, requester=request.user, action=action)

    messages.success(request, "Р—Р°СЏРІРєР° РѕС‚РїСЂР°РІР»РµРЅР°!")
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('requests')


@login_required
@require_http_methods(["POST"])
def push_subscribe(request):
    # РЎРѕС…СЂР°РЅСЏРµС‚ push-РїРѕРґРїРёСЃРєСѓ Р±СЂР°СѓР·РµСЂР° РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ Рё РІРѕР·РІСЂР°С‰Р°РµС‚ JSON СЃРѕ СЃС‚Р°С‚СѓСЃРѕРј.
    """РЎРѕС…СЂР°РЅСЏРµС‚ push-РїРѕРґРїРёСЃРєСѓ Р±СЂР°СѓР·РµСЂР°."""
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
    # РЈРґР°Р»СЏРµС‚ push-РїРѕРґРїРёСЃРєСѓ Р±СЂР°СѓР·РµСЂР° Рё РІРѕР·РІСЂР°С‰Р°РµС‚ JSON СЃРѕ СЃС‚Р°С‚СѓСЃРѕРј РѕРїРµСЂР°С†РёРё.
    """РЈРґР°Р»СЏРµС‚ push-РїРѕРґРїРёСЃРєСѓ Р±СЂР°СѓР·РµСЂР°."""
    try:
        data = json.loads(request.body)
        PushSubscription.objects.filter(endpoint=data['endpoint']).delete()
        return JsonResponse({'ok': True})
    except Exception:
        return JsonResponse({'ok': False}, status=400)


@login_required
def chat_list(request, chat_id=None):
    # РџРѕРєР°Р·С‹РІР°РµС‚ СЃРїРёСЃРѕРє С‡Р°С‚РѕРІ Рё РІС‹Р±СЂР°РЅРЅС‹Р№ С‡Р°С‚, РїРѕРјРµС‡Р°РµС‚ РІС…РѕРґСЏС‰РёРµ РєР°Рє РїСЂРѕС‡РёС‚Р°РЅРЅС‹Рµ, РІРѕР·РІСЂР°С‰Р°РµС‚ HTML.
    """РЎРїРёСЃРѕРє РІСЃРµС… С‡Р°С‚РѕРІ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ СЃ РґРµС‚Р°Р»СЏРјРё РІС‹Р±СЂР°РЅРЅРѕРіРѕ С‡Р°С‚Р°"""
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

    # РњРѕР±РёР»СЊРЅР°СЏ РєРЅРѕРїРєР° В«РќР°Р·Р°РґВ» РІ С‡Р°С‚Рµ: /chat/?list=1 вЂ” С‚РѕР»СЊРєРѕ СЃРїРёСЃРѕРє, Р±РµР· Р°РІС‚РѕРІС‹Р±РѕСЂР° РїРµСЂРІРѕРіРѕ С‡Р°С‚Р°
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
    # РћС‚РєСЂС‹РІР°РµС‚ РєРѕРЅРєСЂРµС‚РЅС‹Р№ С‡Р°С‚, РѕС‚РјРµС‡Р°РµС‚ СЃРѕРѕР±С‰РµРЅРёСЏ РєР°Рє РїСЂРѕС‡РёС‚Р°РЅРЅС‹Рµ Рё РІРѕР·РІСЂР°С‰Р°РµС‚ СЃС‚СЂР°РЅРёС†Сѓ С‡Р°С‚Р°.
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
    # РћС‚РїСЂР°РІР»СЏРµС‚ СЃРѕРѕР±С‰РµРЅРёРµ/РёР·РѕР±СЂР°Р¶РµРЅРёРµ РІ С‡Р°С‚ Рё РІРѕР·РІСЂР°С‰Р°РµС‚ redirect РѕР±СЂР°С‚РЅРѕ Рє СЃРїРёСЃРєСѓ С‡Р°С‚РѕРІ.
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    text = request.POST.get('text', '').strip()
    image = request.FILES.get('image')

    if not text and not image:
        messages.error(request, "РЎРѕРѕР±С‰РµРЅРёРµ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј")
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
    # Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃРѕРѕР±С‰РµРЅРёСЏ РІС‹Р±СЂР°РЅРЅРѕРіРѕ С‡Р°С‚Р° РІ JSON Рё РїРѕРјРµС‡Р°РµС‚ РІС…РѕРґСЏС‰РёРµ РєР°Рє РїСЂРѕС‡РёС‚Р°РЅРЅС‹Рµ.
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
    # РЎРѕР·РґР°РµС‚ РЅРѕРІС‹Р№ С‡Р°С‚ РёР»Рё РѕС‚РєСЂС‹РІР°РµС‚ СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёР№ Рё РІРѕР·РІСЂР°С‰Р°РµС‚ redirect РЅР° С‡Р°С‚.
    other_user = get_object_or_404(User, id=user_id)

    if other_user == request.user:
        messages.error(request, "РќРµР»СЊР·СЏ РЅР°С‡Р°С‚СЊ С‡Р°С‚ СЃ СЃР°РјРёРј СЃРѕР±РѕР№")
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
