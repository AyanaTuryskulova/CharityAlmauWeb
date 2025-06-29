from django import forms
from .models import Product, Category

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'phone', 'title', 'description', 'type', 'main_category', 'subcategory', 'sub_subcategory', 'image']
