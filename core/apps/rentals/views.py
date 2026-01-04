from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages

from .models import RentItem
from core.models import Product
from core.models import TradeRequest


@login_required
def rentals_list(request):
    """Список всех доступных товаров для аренды"""
    # Получаем все товары типа "rental" которые доступны
    # Исключаем товары текущего пользователя
    available_products = Product.objects.filter(
        type='rental',
        status='available',
        is_approved=True
    ).exclude(user=request.user)
    
    # Получаем ID товаров, которые уже арендуются (активная аренда)
    rented_product_ids = RentItem.objects.filter(
        status='rented'
    ).values_list('product_id', flat=True)
    
    # Фильтруем только те товары, которые доступны (не арендуются)
    available_products = available_products.exclude(id__in=rented_product_ids)
    
    # Формируем данные для JSON API
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
        
        return JsonResponse({
            'products': products_data,
        })
    
    # Обычный HTML view
    return render(request, 'rentals/index.html', {
        'products': available_products,
    })


@login_required
def my_rentals(request):
    """Список всех аренд пользователя"""
    # Аренды, где пользователь - арендатор
    rented_items = RentItem.objects.filter(renter=request.user)
    
    # Аренды, где пользователь - владелец товара
    owned_rentals = RentItem.objects.filter(owner=request.user)
    
    # Фильтруем по статусу, если передан параметр
    status_filter = request.GET.get('status')
    if status_filter:
        rented_items = rented_items.filter(status=status_filter)
        owned_rentals = owned_rentals.filter(status=status_filter)
    
    # Формируем данные для JSON API
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
    
    # Обычный HTML view
    return render(request, 'rentals/my_rentals.html', {
        'rented_items': rented_items,
        'owned_rentals': owned_rentals,
    })


@login_required
def rental_detail(request, rental_id):
    """Детали аренды"""
    rental = get_object_or_404(
        RentItem,
        id=rental_id
    )
    
    # Проверяем, что пользователь имеет доступ к этой аренде
    if rental.renter != request.user and rental.owner != request.user:
        messages.error(request, "У вас нет доступа к этой аренде")
        return redirect('rentals_list')
    
    # JSON API
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
    
    # HTML view
    return render(request, 'rentals/detail.html', {
        'rental': rental,
        'is_renter': rental.renter == request.user,
        'is_owner': rental.owner == request.user,
    })


@login_required
@require_http_methods(["POST"])
def create_rental(request):
    """Создать новую аренду"""
    product_id = request.POST.get('product_id')
    expected_return_date = request.POST.get('expected_return_date')
    
    if not product_id:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'product_id is required'}, status=400)
        messages.error(request, "Не указан товар")
        return redirect('home')
    
    product = get_object_or_404(Product, id=product_id)
    
    # Нельзя арендовать свой товар
    if product.user == request.user:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'Cannot rent your own product'}, status=400)
        messages.error(request, "Нельзя арендовать свой товар")
        return redirect('product_detail', product_id=product_id)
    
    # Проверяем, нет ли уже активной аренды
    existing_rental = RentItem.objects.filter(
        product=product,
        renter=request.user,
        status='rented'
    ).first()
    
    if existing_rental:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'Active rental already exists'}, status=400)
        messages.error(request, "У вас уже есть активная аренда этого товара")
        return redirect('rental_detail', rental_id=existing_rental.id)
    
    # Создаем аренду
    rental = RentItem.objects.create(
        product=product,
        renter=request.user,
        owner=product.user,
        expected_return_date=expected_return_date if expected_return_date else None,
    )

    # Создаём/гарантируем наличие заявки для отображения в общем списке заявок
    tr, created_tr = TradeRequest.objects.get_or_create(
        product=product,
        requester=request.user,
        owner=product.user,
        action='rent',
        defaults={'status': 'pending'}
    )
    # Если заявка уже есть, но имеет статус cancelled/rejected, можно восстановить её в pending
    if not created_tr and tr.status in ('rejected', 'cancelled'):
        tr.status = 'pending'
        tr.save()

    # Обновляем статус продукта (по аналогии с запросом на взятие)
    product.status = 'taken'
    product.save()
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'id': rental.id,
            'message': 'Rental created successfully',
        }, status=201)
    
    messages.success(request, "Аренда создана")
    return redirect('rental_detail', rental_id=rental.id)


@login_required
@require_http_methods(["POST", "PATCH"])
def update_rental(request, rental_id):
    """Обновить статус аренды"""
    rental = get_object_or_404(RentItem, id=rental_id)
    
    # Проверяем права доступа
    if rental.renter != request.user and rental.owner != request.user:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'Access denied'}, status=403)
        messages.error(request, "У вас нет доступа к этой аренде")
        return redirect('rentals_list')
    
    # Получаем новый статус
    if request.method == 'POST':
        new_status = request.POST.get('status')
    else:  # PATCH
        import json
        data = json.loads(request.body)
        new_status = data.get('status')
    
    if not new_status:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'status is required'}, status=400)
        messages.error(request, "Не указан статус")
        return redirect('rental_detail', rental_id=rental_id)
    
    # Обновляем статус
    old_status = rental.status
    rental.status = new_status
    
    # Если статус "returned", устанавливаем end_date
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
    
    messages.success(request, f"Статус аренды изменен с '{rental.get_status_display()}' на '{rental.get_status_display()}'")
    return redirect('rental_detail', rental_id=rental_id)
