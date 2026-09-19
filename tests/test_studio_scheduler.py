from backgroundpxr.studio_v047 import DeferredStudioUpdates


class FakeRoot:
    def __init__(self):
        self.callbacks = {}
        self.cancelled = []
        self._counter = 0

    def after(self, delay, callback):
        self._counter += 1
        ident = f"after-{self._counter}"
        self.callbacks[ident] = (delay, callback)
        return ident

    def after_cancel(self, ident):
        self.cancelled.append(ident)
        self.callbacks.pop(ident, None)

    def fire(self, ident):
        _delay, callback = self.callbacks.pop(ident)
        callback()


def test_render_requests_are_throttled_to_one_pending_frame():
    root = FakeRoot()
    renders = []
    saves = []
    scheduler = DeferredStudioUpdates(root, lambda: renders.append(1), lambda: saves.append(1))

    scheduler.request_render()
    first = scheduler._render_after_id
    scheduler.request_render()
    scheduler.request_render()

    assert scheduler.render_pending
    assert scheduler._render_after_id == first
    assert len(root.callbacks) == 1

    root.fire(first)
    assert renders == [1]
    assert not scheduler.render_pending

    scheduler.request_render()
    assert scheduler.render_pending
    assert scheduler._render_after_id != first


def test_settings_writes_are_debounced_to_trailing_edge():
    root = FakeRoot()
    renders = []
    saves = []
    scheduler = DeferredStudioUpdates(root, lambda: renders.append(1), lambda: saves.append(1))

    scheduler.request_save()
    first = scheduler._save_after_id
    scheduler.request_save()
    second = scheduler._save_after_id

    assert first != second
    assert first in root.cancelled
    assert first not in root.callbacks
    assert scheduler.save_pending

    root.fire(second)
    assert saves == [1]
    assert not scheduler.save_pending


def test_flush_and_cancel_do_not_leave_stale_callbacks():
    root = FakeRoot()
    renders = []
    saves = []
    scheduler = DeferredStudioUpdates(root, lambda: renders.append(1), lambda: saves.append(1))

    scheduler.request_render()
    render_id = scheduler._render_after_id
    scheduler.flush_render()

    assert renders == [1]
    assert render_id in root.cancelled
    assert not scheduler.render_pending

    scheduler.request_save()
    save_id = scheduler._save_after_id
    scheduler.cancel_all()

    assert save_id in root.cancelled
    assert not scheduler.render_pending
    assert not scheduler.save_pending
