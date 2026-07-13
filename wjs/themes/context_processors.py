from importlib.metadata import version


def wjs_themes_version(request):
    """
    Inject package version in the rendering context.

    :param request: the active request
    :return: dictionary containing DATE_FORMAT / DATETIME_FORMAT
    """
    return {
        "WJS_THEMES_VERSION": version("wjs.themes"),
    }
