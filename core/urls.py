from django.urls import path, include
from .views import (
    login_view, register_view, onboarding_view,
    home_view, logout_view, my_ads, edit_product,
    requests_view, add_product, product_detail,
    product_action, get_subcategories, free_list, exchange_list,
    favorite_toggle, infer_product_image,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('free/', free_list, name='free_list'),
    path('exchange/', exchange_list, name='exchange_list'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
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

  
    path('get-subcategories/<int:category_id>/', get_subcategories, name='get_subcategories'),
    path("chat/", include("core.apps.chat.urls")),
    path("rentals/", include("core.apps.rentals.urls")),
    path("profile/", include("core.apps.tenant_profile.urls")),

]
