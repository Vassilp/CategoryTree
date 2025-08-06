import io

from django.contrib import admin
from django.core.management import call_command
from django.db import models
from django.shortcuts import render
from django.urls import path

from .models import Category, Similarity


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')


class SimilarityAdmin(admin.ModelAdmin):
    list_display = ('category_a', 'category_b')


class SimilarityStatsAdmin(admin.ModelAdmin):
    # change_list_template = "admin/similarity_stats.html"
    #
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("stats/", self.admin_site.admin_view(self.changelist_view))
        ]
        return custom_urls + urls

    def get_queryset(self, request):
        return DummyModel.objects.none()  # prevent any DB query

    def changelist_view(self, request, extra_context=None):
        output = io.StringIO()
        call_command("analyze_similarity", stdout=output)
        output.seek(0)

        # Context with correct admin breadcrumbs
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Similarity Analysis",
            "output": output.read(),
        }

        return render(request, "admin/similarity_stats.html", context)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class DummyModel(models.Model):
    class Meta:
        managed = False
        verbose_name = "Similarity Analysis"
        verbose_name_plural = "Similarity Analysis"


admin.site.register(Category, CategoryAdmin)
admin.site.register(Similarity, SimilarityAdmin)
admin.site.register(DummyModel, SimilarityStatsAdmin)
