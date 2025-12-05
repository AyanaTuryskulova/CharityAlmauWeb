from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Max
from django.contrib import messages
from django.urls import reverse

from .models import Chat, Message
from django.contrib.auth.models import User


@login_required
def chat_list(request, chat_id=None):
    """Список всех чатов пользователя с деталями выбранного чата"""
    # Получаем все чаты, где пользователь является участником
    user_chats = Chat.objects.filter(participants=request.user).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time', '-updated_at')
    
    # Для каждого чата получаем последнее сообщение и другого участника
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
    
    # Определяем выбранный чат из URL параметра, GET параметра или берем первый
    selected_chat = None
    selected_other_user = None
    selected_messages = []
    
    # Сначала проверяем URL параметр (chat_id из path), потом GET параметр
    chat_id = chat_id or request.GET.get('chat_id')
    if chat_id:
        try:
            selected_chat = Chat.objects.get(id=chat_id, participants=request.user)
            selected_other_user = selected_chat.get_other_participant(request.user)
            # Помечаем сообщения как прочитанные
            selected_chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
            selected_messages = selected_chat.messages.all()
        except (Chat.DoesNotExist, ValueError):
            pass
    elif chats_with_info:
        # Если чат не выбран, берем первый
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
    """Открыть конкретный чат"""
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    other_user = chat.get_other_participant(request.user)
    
    # Помечаем сообщения как прочитанные
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
    """Отправить сообщение"""
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    text = request.POST.get('text', '').strip()
    image = request.FILES.get('image')
    
    # Сообщение должно содержать либо текст, либо изображение
    if not text and not image:
        messages.error(request, "Сообщение не может быть пустым")
        return redirect(f'{reverse("chat_list")}?chat_id={chat_id}')
    
    message = Message.objects.create(
        chat=chat,
        sender=request.user,
        text=text if text else '',
        image=image if image else None
    )
    
    # Обновляем время последнего обновления чата
    chat.save()  # Это обновит updated_at
    
    messages.success(request, "Сообщение отправлено")
    return redirect(f'{reverse("chat_list")}?chat_id={chat_id}')


@login_required
def get_messages(request, chat_id):
    """Получить сообщения конкретного чата (для AJAX)"""
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    
    messages_list = chat.messages.all()
    
    # Помечаем сообщения как прочитанные
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
    """Начать чат с пользователем"""
    from core.models import Product
    
    other_user = get_object_or_404(User, id=user_id)
    
    if other_user == request.user:
        messages.error(request, "Нельзя начать чат с самим собой")
        return redirect('home')
    
    # Получаем product_id из GET параметров, если есть
    product_id = request.GET.get('product_id')
    product = None
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            pass
    
    # Ищем существующий чат между этими пользователями
    # Если есть product_id, ищем чат с этим товаром
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
    
    # Создаем новый чат
    new_chat = Chat.objects.create(product=product)
    new_chat.participants.add(request.user, other_user)
    
    return redirect(f'{reverse("chat_list")}?chat_id={new_chat.id}')
