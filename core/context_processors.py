"""Template context helpers shared by every page."""

import os

from django.conf import settings


def asset_version(request):
    """Cache-busting token for stylesheets and scripts.

    Static files are served with ``Cache-Control: immutable`` and a long
    ``expires`` (see ``nginx/default.conf``), so the URL has to change whenever
    the file does. Using the stylesheet's mtime means every deploy produces a
    new query string without any manual version bump.
    """

    path = os.path.join(
        settings.BASE_DIR, 'core', 'static', 'core', 'css', 'main.css'
    )
    try:
        return {'asset_version': int(os.path.getmtime(path))}
    except OSError:
        return {'asset_version': 1}