from django.urls import path

from .admin import advanced_admin_site

urlpatterns = [
    path("", advanced_admin_site.urls),
]
