from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _


class AdvancedAdminSite(AdminSite):
    site_header = _("Advanced Administration")
    site_title = _("Advanced Admin")
    index_title = _("Advanced Control Panel")
