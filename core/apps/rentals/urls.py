from django.urls import path
from . import views

urlpatterns = [
    path("", views.rentals_home, name="rentals_home"),
]
