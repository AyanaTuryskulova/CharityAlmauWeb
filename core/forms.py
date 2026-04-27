from django import forms

from .models import Category, Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "title",
            "description",
            "phone",
            "type",
            "main_category",
            "subcategory",
            "sub_subcategory",
            "image",
            "condition",
            "defects",
            "meeting_place",
            "meeting_place_text",
            "price",
            "rent_period",
            "min_rent_time",
            "return_rules",
            "exchange_other",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow backend to auto-fill title from image if user leaves it empty.
        self.fields["title"].required = False

        self.fields["main_category"].queryset = Category.objects.filter(parent__isnull=True)
        self.fields["subcategory"].queryset = Category.objects.none()
        self.fields["sub_subcategory"].queryset = Category.objects.none()

        if "main_category" in self.data:
            try:
                main_id = int(self.data.get("main_category"))
                self.fields["subcategory"].queryset = Category.objects.filter(parent_id=main_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.main_category:
            self.fields["subcategory"].queryset = Category.objects.filter(parent=self.instance.main_category)

        if "subcategory" in self.data:
            try:
                sub_id = int(self.data.get("subcategory"))
                self.fields["sub_subcategory"].queryset = Category.objects.filter(parent_id=sub_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.subcategory:
            self.fields["sub_subcategory"].queryset = Category.objects.filter(parent=self.instance.subcategory)

        # On create flow, images are uploaded via images_0..images_4 inputs.
        if not self.instance.pk:
            self.fields["image"].required = False
        if self.instance.pk:
            self.fields["image"].widget = forms.FileInput(attrs={"accept": "image/*"})
