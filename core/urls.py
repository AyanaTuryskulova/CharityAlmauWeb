from django.urls import path, include
from .views import (
    login_view, register_view, onboarding_view,
    home_view, logout_view, my_ads, edit_product,
    requests_view, add_product, product_detail,
    product_action, get_subcategories
)

urlpatterns = [
    path('', home_view, name='home'),
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

  
    path('get-subcategories/<int:category_id>/', get_subcategories, name='get_subcategories'),
    path("chat/", include("core.apps.chat.urls")),
    path("rentals/", include("core.apps.rentals.urls")),
    path("profile/", include("core.apps.tenant_profile.urls")),

]
