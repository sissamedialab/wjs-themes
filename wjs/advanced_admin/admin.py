import os

from core.files import overwrite_file
from core.models import File, Galley, SupplementaryFile, XSLFile
from django import forms
from django.contrib import admin
from django.http import HttpRequest
from submission.models import Article

from .admin_site import AdvancedAdminSite

advanced_admin_site = AdvancedAdminSite(name="advanced_admin")


class FileForm(forms.ModelForm):
    file_upload = forms.FileField(label="Upload File", required=True)

    class Meta:
        model = File
        fields = ("original_filename", "label", "description", "owner", "mime_type", "uuid_filename", "privacy")

    def save(self, commit=True):
        """
        Save the current instance, handling file uploads if provided.

        If a file is uploaded, it processes and overwrites the file at the appropriate location
        based on the folder structure derived from the instance's paths.

        :param commit: Flag to control whether changes are committed immediately
        :type commit: bool
        :return: The saved instance
        :rtype: object
        :raises AttributeError: If instance paths do not support `os.path.dirname`
        :raises ValueError: If `self.cleaned_data["file_upload"]` is invalid
        :raises OSError: If there is an issue accessing or modifying file paths
        """
        instance = super().save(commit=False)
        if self.cleaned_data["file_upload"]:
            if instance.self_article_path():
                folder_structure = os.path.dirname(instance.self_article_path())  # noqa: PTH120
            else:
                folder_structure = os.path.dirname(instance.journal_path())  # noqa: PTH120
            path_parts = folder_structure.split("/")[-3:]
            overwrite_file(self.cleaned_data["file_upload"], instance, path_parts)
        return instance


@admin.register(File, site=advanced_admin_site)
class FileAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "label", "description")
    search_fields = ("original_filename", "label", "description")
    form = FileForm

    def has_add_permission(self, request: HttpRequest) -> bool:  # noqa: PLR6301
        """
        Determine if the user has permission to add an object.

        Current implementation blocks all users from adding new files.

        :param request: The HTTP request object containing user information and metadata
        :type request: HttpRequest
        :return: False indicating that the user does not have permission to add
        :rtype: bool
        """
        return False


@admin.register(SupplementaryFile, site=advanced_admin_site)
class SupplementaryFileI(admin.ModelAdmin):
    list_display = ("file", "doi")
    search_fields = ("file__original_filename", "doi")


@admin.register(XSLFile, site=advanced_admin_site)
class XSLFileAdmin(admin.ModelAdmin):
    list_display = ("label",)
    search_fields = ("file__original_filename",)


class GalleyInline(admin.StackedInline):
    model = Galley
    autocomplete_fields = ("file", "css_file", "images", "xsl_file")
    extra = 0
    fields = ("label", "type", "sequence", "file", "css_file", "images", "xsl_file", "public")


@admin.register(Article, site=advanced_admin_site)
class ArticleAdmin(admin.ModelAdmin):
    readonly_fields = ("title",)
    fields = (
        "title",
        "source_files",
        "manuscript_files",
        "data_figure_files",
        "supplementary_files",
        "date_published",
        "comments_editor",
    )
    autocomplete_fields = ("source_files", "manuscript_files", "data_figure_files", "supplementary_files")
    list_display = ["title", "pubid", "journal", "state", "identifier"]
    list_filter = ["journal", "articleworkflow__state"]
    ordering = ("-pk",)
    search_fields = ("identifier__identifier", "pk")
    inlines = (GalleyInline,)

    def has_add_permission(self, request: HttpRequest) -> bool:  # noqa: PLR6301
        """
        Determine if the user has permission to add an object.

        Current implementation blocks all users from adding new articles.

        :param request: The HTTP request object containing user information and metadata
        :type request: HttpRequest
        :return: False indicating that the user does not have permission to add
        :rtype: bool
        """
        return False

    def state(self, obj: Article) -> str:  # noqa: PLR6301
        """
        Retrieve the display name of the current state of the object's workflow.

        :param obj: The object whose workflow state display name is retrieved
        :type obj: Article
        :return: The display name of the current state of the object's workflow
        :rtype: str
        """
        return obj.articleworkflow.get_state_display() if hasattr(obj, "articleworkflow") else None

    def pubid(self, obj: Article) -> str:  # noqa: PLR6301
        """
        Retrieve the pubid of the article.

        :param obj: The object whose workflow state display name is retrieved
        :type obj: Article
        :return: The pubid of the article
        :rtype: str
        """
        return obj.get_pubid()
