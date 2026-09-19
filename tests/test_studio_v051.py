from types import SimpleNamespace

from backgroundpxr.studio_v051 import (
    PREVIEW_RESIZE_DEBOUNCE_MS,
    BackgroundPXRStudio051App,
)


class FakeRoot:
    def __init__(self):
        self.callbacks = {}
        self.cancelled = []
        self._next = 0

    def after(self, delay, callback):
        self._next += 1
        token = f"after-{self._next}"
        self.callbacks[token] = (delay, callback)
        return token

    def after_cancel(self, token):
        self.cancelled.append(token)
        self.callbacks.pop(token, None)


def make_app():
    app = object.__new__(BackgroundPXRStudio051App)
    app.root = FakeRoot()
    app._preview_resize_after_id = None
    app._preview_canvas_sizes = {}
    app.refreshes = 0
    app._refresh_previews = lambda: setattr(app, "refreshes", app.refreshes + 1)
    return app


def test_preview_resize_is_debounced_and_refreshes_after_geometry_settles():
    app = make_app()
    widget = object()

    app._on_preview_canvas_configure(SimpleNamespace(widget=widget, width=420, height=600))
    first = app._preview_resize_after_id
    assert first is not None
    assert app.root.callbacks[first][0] == PREVIEW_RESIZE_DEBOUNCE_MS

    # Duplicate Configure noise for the same geometry should do nothing.
    app._on_preview_canvas_configure(SimpleNamespace(widget=widget, width=420, height=600))
    assert app._preview_resize_after_id == first
    assert app.root.cancelled == []

    # A real resize replaces the stale pending render with the newest geometry.
    app._on_preview_canvas_configure(SimpleNamespace(widget=widget, width=260, height=600))
    second = app._preview_resize_after_id
    assert second != first
    assert first in app.root.cancelled

    _delay, callback = app.root.callbacks[second]
    callback()
    assert app.refreshes == 1
    assert app._preview_resize_after_id is None


def test_independent_preview_canvases_share_one_final_refresh():
    app = make_app()
    before = object()
    after = object()

    app._on_preview_canvas_configure(SimpleNamespace(widget=before, width=300, height=500))
    first = app._preview_resize_after_id
    app._on_preview_canvas_configure(SimpleNamespace(widget=after, width=302, height=500))
    second = app._preview_resize_after_id

    assert first in app.root.cancelled
    assert second in app.root.callbacks
    app.root.callbacks[second][1]()
    assert app.refreshes == 1
