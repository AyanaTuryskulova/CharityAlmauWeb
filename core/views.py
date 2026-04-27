# core/views.py

import logging
import json

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
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.conf import settings as django_settings

from .models import Category, Product, ProductImage, TradeRequest, Favorite, Chat, Message, PushSubscription, RentItem
from .forms import ProductForm
from .services.image_autofill import infer_product_from_image
from .notifications import notify_trade_request
from .email_utils import notify_new_message


def switch_language(request, lang_code):
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

    product_type = request.GET.get('type', 'all')
    if product_type not in ('free', 'exchange', 'rental', 'all'):
        product_type = 'all'

    q = (request.GET.get('q') or '').strip()

    qs = Product.objects.filter(is_approved=True).order_by('-created_at')
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
        # Фильтр в Python: регистронезависимый поиск для любого языка и БД
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

    cats = Category.objects.filter(parent__isnull=True)
    return render(request, 'home.html', {
        'products': qs,
        'main_categories': cats,
        'selected_id': selected_id,
        'selected_type': product_type,
        'search_query': q,
        'favorite_ids': _get_favorite_ids(request),
        'weekly_new_count': weekly_new_count,
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

    selected_status = request.GET.get('status', 'all')
    if selected_status not in ('all', 'pending', 'active', 'rejected'):
        selected_status = 'all'

    own_products = Product.objects.filter(user=request.user)
    if selected_status == 'pending':
        own_products = own_products.filter(is_approved=False)
    elif selected_status == 'active':
        own_products = own_products.filter(is_approved=True)
    elif selected_status == 'rejected':
        own_products = own_products.filter(status='rejected')

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
        'selected_status': selected_status,
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

            #  ОБМЕН (checkbox)
            exchange = request.POST.getlist('exchange_categories')
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
        messages.info(request, "Избранное пока недоступно.")

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

    # Уведомление автору объявления (push + email)
    notify_trade_request(product=product, requester=request.user, action=action)

    messages.success(request, "Заявка отправлена!")
    return redirect('requests')


def profile_home(request):
    return render(request, "profile/index.html")


@login_required
@require_http_methods(["POST"])
def push_subscribe(request):
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
    """Удаляет push-подписку браузера."""
    try:
        data = json.loads(request.body)
        PushSubscription.objects.filter(endpoint=data['endpoint']).delete()
        return JsonResponse({'ok': True})
    except Exception:
        return JsonResponse({'ok': False}, status=400)


@login_required
def chat_list(request, chat_id=None):
    """Список всех чатов пользователя с деталями выбранного чата"""
    user_chats = Chat.objects.filter(participants=request.user).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time', '-updated_at')

    chats_with_info = []
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

    selected_chat = None
    selected_other_user = None
    selected_messages = []

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
        'selected_chat': selected_chat,
        'selected_other_user': selected_other_user,
        'selected_messages': selected_messages,
    })


@login_required
def chat_detail(request, chat_id):
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

    messages.success(request, "Сообщение отправлено")
    return redirect(f'{reverse("chat_list")}?chat_id={chat_id}')


@login_required
def get_messages(request, chat_id):
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
def start_chat(request, user_id):
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
def my_rentals(request):
    rented_items = RentItem.objects.filter(renter=request.user)
    owned_rentals = RentItem.objects.filter(owner=request.user)

    status_filter = request.GET.get('status')
    if status_filter:
        rented_items = rented_items.filter(status=status_filter)
        owned_rentals = owned_rentals.filter(status=status_filter)

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        rented_data = [{
            'id': item.id,
            'product': {
                'id': item.product.id,
                'title': item.product.title,
                'image': item.product.image.url if item.product.image else None,
            },
            'owner': {
                'id': item.owner.id,
                'username': item.owner.username,
            },
            'status': item.status,
            'status_display': item.get_status_display(),
            'start_date': item.start_date.isoformat(),
            'end_date': item.end_date.isoformat() if item.end_date else None,
            'expected_return_date': item.expected_return_date.isoformat() if item.expected_return_date else None,
        } for item in rented_items]

        owned_data = [{
            'id': item.id,
            'product': {
                'id': item.product.id,
                'title': item.product.title,
                'image': item.product.image.url if item.product.image else None,
            },
            'renter': {
                'id': item.renter.id,
                'username': item.renter.username,
            },
            'status': item.status,
            'status_display': item.get_status_display(),
            'start_date': item.start_date.isoformat(),
            'end_date': item.end_date.isoformat() if item.end_date else None,
            'expected_return_date': item.expected_return_date.isoformat() if item.expected_return_date else None,
        } for item in owned_rentals]

        return JsonResponse({
            'rented_items': rented_data,
            'owned_rentals': owned_data,
        })

    return render(request, 'rentals/my_rentals.html', {
        'rented_items': rented_items,
        'owned_rentals': owned_rentals,
    })


@login_required
def rental_detail(request, rental_id):
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
