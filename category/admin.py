from django.contrib import admin

from .models import Category, Similarity


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'parent')


class SimilarityAdmin(admin.ModelAdmin):
    list_display = ('category_a', 'category_b')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Similarity, SimilarityAdmin)
