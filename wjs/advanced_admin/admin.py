import os
import uuid
from urllib.parse import urlencode

from core.files import overwrite_file
from core.model_utils import DateTimePickerInput, DateTimePickerModelField
from core.models import File, Galley, SupplementaryFile, XSLFile
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.core.files import File as DjangoFile
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from submission.models import Article
from typesetting.models import GalleyProofing

from .admin_site import AdvancedAdminSite

advanced_admin_site = AdvancedAdminSite(name="advanced_admin")


class ParamsWrapper(RelatedFieldWidgetWrapper):
    def __init__(self, wrapper, extra):
        """
        Add wrapper to wrap some extra context to url params.
        """
        super().__init__(
            wrapper.widget,
            wrapper.rel,
            wrapper.admin_site,
            wrapper.can_add_related,
            wrapper.can_change_related,
            wrapper.can_delete_related,
            wrapper.can_view_related,
        )
        self.extra = extra

    def get_context(self, name, value, attrs):
        """
        Add extra context to url params.
        """
        ctx = super().get_context(name, value, attrs)
        ctx["url_params"] += "&" + urlencode(self.extra)
        return ctx


class FileProxy(File):
    class Meta:
        proxy = True
        verbose_name = _("Manuscript file, ESM and admin file")
        verbose_name_plural = _("Manuscript files, ESM and admin files")


class SupplementaryFileProxy(SupplementaryFile):
    class Meta:
        proxy = True
        verbose_name = _("ESM")
        verbose_name_plural = _("ESM")


class GalleyProofingProxy(GalleyProofing):
    class Meta:
        proxy = True
        verbose_name = _("Author's proofreading")
        verbose_name_plural = _("Author's proofreadings")


class FileSaveMixin:
    @staticmethod
    def file_save(instance, file_upload, journal) -> None:
        """
        Save file for the current instance, handling correct file path.
        """
        if instance.self_article_path():
            folder_structure = os.path.dirname(instance.self_article_path())  # noqa: PTH120
        else:
            folder_structure = os.path.dirname(instance.journal_path(journal=journal))  # noqa: PTH120
        path_parts = folder_structure.split("/")[-2:]
        overwrite_file(file_upload, instance, path_parts)


class FileProxyForm(FileSaveMixin, forms.ModelForm):
    label = forms.CharField(label="Label", required=True)
    file_upload = forms.FileField(label="Upload File", required=True)

    class Meta:
        model = FileProxy
        fields = ("original_filename", "description", "owner", "mime_type", "uuid_filename", "privacy")

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
            journal = instance.article.journal if instance.article else None
            self.file_save(instance=instance, file_upload=self.cleaned_data["file_upload"], journal=journal)
        return instance


@admin.register(FileProxy, site=advanced_admin_site)
class FileAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "label", "description")
    search_fields = ("original_filename", "label", "description")
    form = FileProxyForm

    def get_queryset(self, request):
        """
        Filter queryset excluding files without article_id.
        """
        qs = super().get_queryset(request)
        return qs.exclude(article_id=None)

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


@admin.register(SupplementaryFileProxy, site=advanced_admin_site)
class SupplementaryFileI(admin.ModelAdmin):
    list_display = ("file", "doi")
    search_fields = ("file__original_filename", "doi")
    autocomplete_fields = ("file",)


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
class ArticleAdmin(FileSaveMixin, admin.ModelAdmin):
    LABELS = {
        "data_figure_files": "Administrative files",
        "comments_editor": "Author's cover letter (v1)",
    }
    FILE_FIELDS = ("source_files", "manuscript_files", "data_figure_files", "supplementary_files")

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

    autocomplete_fields = FILE_FIELDS
    list_display = ["title", "pubid", "journal", "state", "identifier_display"]
    ordering = ("-pk",)
    search_fields = ("identifier__identifier", "pk")
    inlines = (GalleyInline,)

    formfield_overrides = {
        DateTimePickerModelField: {"widget": DateTimePickerInput},
    }

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """
        Set correct labels.
        """
        if db_field.name in self.LABELS:
            kwargs["label"] = self.LABELS[db_field.name]
        ff = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in self.FILE_FIELDS:
            object_id = request.resolver_match.kwargs.get("object_id")
            if object_id:
                ff.widget = ParamsWrapper(ff.widget, {"article": object_id})
        return ff

    def get_list_filter(self, request: HttpRequest) -> list[str]:  # noqa: PLR6301
        """
        Retrieve the list of filters to be applied in the list view.

        :param request: The current HTTP request object
        :type request: HttpRequest
        :return: A list of filter fields
        :rtype: list
        """
        return ["journal", "articleworkflow__state"]

    @admin.display(description="identifier")
    def identifier_display(self, obj: Article) -> str:  # noqa: PLR6301
        """
        Return the article's identifier for the admin list display.

        Not named "identifier" directly: identifiers.Identifier.article has no related_name,
        so its reverse query name is also "identifier", which Django 5.x's admin.E109 check
        now flags when a list_display item resolves to a reverse FK relation instead of a
        plain attribute. Renaming this display method sidesteps the field lookup entirely.
        """
        return obj.identifier

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

    def save_related(self, request, form, formsets, change):
        """
        Recalculate the file path of the article file.
        """
        super().save_related(request, form, formsets, change)
        changed = [f for f in self.FILE_FIELDS if f in form.changed_data]
        for field in changed:
            self.recalc_file_path(article=form.instance, field_name=field)

    def recalc_file_path(self, article, field_name) -> None:
        """
        Recalculate the file path of the article file with the given field name.
        """
        files = getattr(article, field_name).all()
        for article_file in files:
            if field_name == "supplementary_files":
                article_file = article_file.file  # noqa: PLW2901

            if article_file.article_id and article_file.article_id != article.pk:
                old_article = Article.objects.get(pk=article_file.article_id)
                file_upload_path = article_file.get_file_path(old_article)
                if os.path.isfile(file_upload_path):  # noqa: PTH113
                    with open(file_upload_path, "rb") as f:  # noqa: PTH123
                        file_upload = DjangoFile(f, name=os.path.basename(file_upload_path))  # noqa: PTH119

                        article_file.article_id = article.pk
                        article_file.uuid_filename = str(uuid.uuid4())
                        article_file.save()
                        self.file_save(instance=article_file, file_upload=file_upload, journal=article.journal)
                    os.unlink(file_upload_path)  # noqa: PTH108


@admin.register(GalleyProofingProxy, site=advanced_admin_site)
class GalleyProofingAdmin(admin.ModelAdmin):
    """
    Admin interface for managing GalleyProofing notes.
    """

    fields = ("notes",)
    list_display = ("article_pubid", "article_title", "article_journal", "manager", "proofreader", "round")

    list_filter = ("round__article__journal",)
    search_fields = (
        "round__article__identifier__identifier",
        "manager__email",
        "proofreader__email",
    )

    def article_pubid(self, obj: GalleyProofing) -> str:  # noqa: PLR6301
        """
        Retrieve the Article.pubid.

        :param obj: The object whose workflow state display name is retrieved
        :type obj: GalleyProofing
        :return: The pubid of the round article
        :rtype: str
        """
        return obj.round.article.get_pubid()

    def article_title(self, obj: GalleyProofing) -> str:  # noqa: PLR6301
        """
        Retrieve the Article.title.

        :param obj: The object whose workflow state display name is retrieved
        :type obj: GalleyProofing
        :return: The title of the round article
        :rtype: str
        """
        return obj.round.article.title

    def article_journal(self, obj: GalleyProofing) -> str:  # noqa: PLR6301
        """
        Retrieve the Article.journal.

        :param obj: The object whose workflow state display name is retrieved
        :type obj: GalleyProofing
        :return: The journal of the round article
        :rtype: str
        """
        return obj.round.article.journal.name if obj.round.article.journal else None


@admin.register(SupplementaryFile, site=advanced_admin_site)
class SupplementaryFileAutocompleteAdmin(admin.ModelAdmin):
    search_fields = ("doi", "file__original_filename", "file__description", "file__label")

    def has_module_permission(self, request):  # noqa: PLR6301
        """
        Do not show it by default.
        """
        return False


class FileForm(forms.ModelForm):
    label = forms.CharField(label="Label", required=True)
    file_upload = forms.FileField(label="Upload File", required=True)

    class Meta:
        model = File
        fields = ("original_filename", "description", "owner", "privacy")


@admin.register(File, site=advanced_admin_site)
class FileAutocompleteAdmin(FileSaveMixin, admin.ModelAdmin):
    search_fields = ("original_filename", "label", "description")

    form = FileForm

    def get_queryset(self, request):
        """
        Filter queryset excluding files without article_id.
        """
        qs = super().get_queryset(request)
        return qs.exclude(article_id=None)

    def has_module_permission(self, request):  # noqa: PLR6301
        """
        Do not show it by default.
        """
        return False

    def save_model(self, request, obj, form, change):
        """
        Write file in the right path.
        """
        super().save_model(request, obj, form, change)
        if not change and not obj.article_id:
            obj.article_id = int(request.GET["article"])

            file_upload = form.cleaned_data.get("file_upload")

            if file_upload:
                obj.uuid_filename = str(uuid.uuid4())
                obj.save()
                self.file_save(instance=obj, file_upload=file_upload, journal=request.journal)

    class Meta:
        model = File
