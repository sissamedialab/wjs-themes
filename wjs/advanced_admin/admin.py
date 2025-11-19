from django.contrib import admin
from submission.models import Article

from .admin_site import AdvancedAdminSite

advanced_admin_site = AdvancedAdminSite(name="advanced_admin")


@admin.register(Article, site=advanced_admin_site)
class ArticleAdmin(admin.ModelAdmin):
    search_fields = ("title",)
