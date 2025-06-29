from django.urls import path
from .views import register_view, login_view, logout_view, home_view, onboarding_view, add_product, get_subcategories, product_detail


urlpatterns = [
    path('', onboarding_view, name='onboarding'), 
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('home/', home_view, name='home'),
    path('add/', add_product, name='add_product'),
    path('get-subcategories/<int:category_id>/', get_subcategories, name='get_subcategories'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),



]
