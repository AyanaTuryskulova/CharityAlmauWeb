from django import forms
from .models import Product, Category

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'title',
            'description',
            'phone',
            'type',
            'main_category',
            'subcategory',
            'sub_subcategory',
            'image'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Отображать только корневые категории в "Основной категории"
        self.fields['main_category'].queryset = Category.objects.filter(parent__isnull=True)

        # По умолчанию скрываем подкатегории (отображаются через JS)
        self.fields['subcategory'].queryset = Category.objects.none()
        self.fields['sub_subcategory'].queryset = Category.objects.none()

        # Если пользователь выбрал основную категорию — показываем подкатегории
        if 'main_category' in self.data:
            try:
                main_id = int(self.data.get('main_category'))
                self.fields['subcategory'].queryset = Category.objects.filter(parent_id=main_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.main_category:
            self.fields['subcategory'].queryset = Category.objects.filter(parent=self.instance.main_category)

        # Если пользователь выбрал подкатегорию — показываем под-подкатегории
        if 'subcategory' in self.data:
            try:
                sub_id = int(self.data.get('subcategory'))
                self.fields['sub_subcategory'].queryset = Category.objects.filter(parent_id=sub_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.subcategory:
            self.fields['sub_subcategory'].queryset = Category.objects.filter(parent=self.instance.subcategory)
