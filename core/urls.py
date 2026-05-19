from django.urls import path
from .views import (
    login_view, onboarding_view,
    home_view, home_feed, catalog_view, logout_view, my_ads, edit_product,
    requests_view, add_product, product_detail,
    product_action, get_subcategories,
    favorite_toggle, infer_product_image, switch_language,
    chat_list, chat_detail, send_message, get_messages,
    start_chat, delete_chat, push_subscribe, push_unsubscribe,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('home/feed/', home_feed, name='home_feed'),
    path('catalog/', catalog_view, name='catalog'),
    path('login/', login_view, name='login'),
    path('onboarding/', onboarding_view, name='onboarding'),
    path('logout/', logout_view, name='logout'),

    path('my_ads/', my_ads, name='my_ads'),
    path('edit/<int:product_id>/', edit_product, name='edit_product'),
    path('requests/', requests_view, name='requests'),
    path('add/', add_product, name='add_product'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('product/<int:product_id>/<str:action>/', product_action, name='product_action'),
    path('favorite/<int:product_id>/', favorite_toggle, name='favorite_toggle'),
    path('infer-product-image/', infer_product_image, name='infer_product_image'),
    path('lang/<str:lang_code>/', switch_language, name='switch_language'),

    path('get-subcategories/<int:category_id>/', get_subcategories, name='get_subcategories'),

    # Chat
    path("chat/", chat_list, name="chat_list"),
    path("chat/start/<int:user_id>/", start_chat, name="start_chat"),
    path("chat/detail/<int:chat_id>/", chat_detail, name="chat_detail"),
    path("chat/messages/<int:chat_id>/", get_messages, name="get_messages"),
    path("chat/<int:chat_id>/send/", send_message, name="send_message"),
    path("chat/<int:chat_id>/delete/", delete_chat, name="delete_chat"),
    path("chat/<int:chat_id>/", chat_list, name="chat_list_with_id"),
    path("chat/push/subscribe/", push_subscribe, name="push_subscribe"),
    path("chat/push/unsubscribe/", push_unsubscribe, name="push_unsubscribe"),
]
