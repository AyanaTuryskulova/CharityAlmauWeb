from django.urls import path
from . import views

urlpatterns = [
    path("", views.rentals_list, name="rentals_list"),
    path("my/", views.my_rentals, name="my_rentals"),
    path("create/", views.create_rental, name="create_rental"),
    path("update/<int:rental_id>/", views.update_rental, name="update_rental"),
    path("<int:rental_id>/", views.rental_detail, name="rental_detail"),
]
