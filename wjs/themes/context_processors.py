from importlib.metadata import version

from tinymce.settings import get_js_url


def wjs_themes_version(request):
    """
    Inject the theme package version and the TinyMCE script URL in the rendering context.

    TINYMCE_JS_URL is taken from django-tinymce itself, so that the script tag in
    base.html always points at the very same URL that django-tinymce emits through
    form.media: a mismatch would load TinyMCE twice and leave tinymce.baseURL
    depending on which tag ran last.

    :param request: the active request
    :return: dictionary containing WJS_THEMES_VERSION / TINYMCE_JS_URL
    """
    return {
        "WJS_THEMES_VERSION": version("wjs.themes"),
        "TINYMCE_JS_URL": get_js_url(),
    }
