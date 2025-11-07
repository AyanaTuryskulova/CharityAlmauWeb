from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_list, name="chat_list"),
    path("start/<int:user_id>/", views.start_chat, name="start_chat"),
    path("detail/<int:chat_id>/", views.chat_detail, name="chat_detail"),
    path("messages/<int:chat_id>/", views.get_messages, name="get_messages"),
    path("<int:chat_id>/send/", views.send_message, name="send_message"),
    path("<int:chat_id>/", views.chat_list, name="chat_list_with_id"),
]
