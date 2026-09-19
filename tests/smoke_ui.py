from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backgroundpxr.display import plan_window
from backgroundpxr.studio_v047 import BackgroundPXRStudio047App
from backgroundpxr.ui import create_root


def _font_size(widget) -> int:
    font = widget.cget("font")
    try:
        return abs(int(font.cget("size")))
    except Exception:
        return 0


def _page_fits(page, widgets):
    page.update_idletasks()
    height = page.winfo_height()
    bottoms = [w.winfo_y() + w.winfo_height() for w in widgets]
    return height, max(bottoms, default=0)


def _smoke_size() -> tuple[int, int]:
    value = os.environ.get("PXR_SMOKE_SIZE", "1600x900").strip().lower()
    try:
        width_text, height_text = value.split("x", 1)
        width = int(width_text)
        height = int(height_text)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid PXR_SMOKE_SIZE={value!r}; expected WIDTHxHEIGHT"
        ) from exc
    if width < 1024 or height < 640:
        raise ValueError(
            f"PXR_SMOKE_SIZE={value!r} is below the supported acceptance floor"
        )
    return width, height


def _assert_inside_root(root, widget, *, label: str) -> None:
    root.update_idletasks()
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    x = widget.winfo_rootx() - root_x
    y = widget.winfo_rooty() - root_y
    right = x + widget.winfo_width()
    bottom = y + widget.winfo_height()
    root_w = root.winfo_width()
    root_h = root.winfo_height()
    tolerance = 3
    assert x >= -tolerance, f"{label} clipped on left: x={x}"
    assert y >= -tolerance, f"{label} clipped on top: y={y}"
    assert right <= root_w + tolerance, (
        f"{label} clipped on right: {right}>{root_w}"
    )
    assert bottom <= root_h + tolerance, (
        f"{label} clipped on bottom: {bottom}>{root_h}"
    )


def main() -> None:
    target_width, target_height = _smoke_size()
    placement = plan_window(target_width, target_height)

    root = create_root()
    root.withdraw()
    app = BackgroundPXRStudio047App(root)

    try:
        root.state("normal")
    except Exception:
        pass

    # CI normally runs on one fixed Windows desktop. Reapply the minimum that
    # BackgroundPXR would choose for the requested logical desktop so the same
    # process can exercise 100%, 125% and 150% scaling-class window sizes.
    root.minsize(placement.min_width, placement.min_height)
    root.geometry(f"{target_width}x{target_height}+0+0")
    # Windows applies top-level geometry asynchronously. A full update is
    # required here; update_idletasks() alone can leave the previous minimum
    # size visible to winfo_width()/winfo_height() on hosted runners.
    root.update_idletasks()
    root.update()
    root.update_idletasks()

    assert abs(root.winfo_width() - target_width) <= 2, (
        f"Unexpected test width: {root.winfo_width()} != {target_width}"
    )
    assert abs(root.winfo_height() - target_height) <= 2, (
        f"Unexpected test height: {root.winfo_height()} != {target_height}"
    )

    required = [
        app.before_canvas,
        app.after_canvas,
        app.remove_btn,
        app.restore_btn,
        app.erase_btn,
        app.export_btn,
        app.footer_github,
        app._diag_percent_label,
        app._diag_button,
        app.left_panel,
        app.studio_mode_bar,
        app.studio_modes_label,
        app.filmstrip_toggle,
        app.inspector_tabs,
        app.subject_card,
        app.style_card,
        app.preview_selector,
        app.spill_switch,
        app.spill_strength_slider,
        app.wipe_frame,
        app.wipe_slider,
        app.wipe_value_label,
        app.mask_overlay_switch,
        app.undo_mask_btn,
        app.redo_mask_btn,
        app.export_mask_btn,
        app.lang,
    ]
    assert all(widget is not None and widget.winfo_exists() for widget in required)
    assert app._diag_percent_var.get() == "0%"
    assert app.diagnostics.path.name == "backgroundpxr.log"
    assert app._last_brush_point is None
    assert app._live_recompose_after_id is None
    assert not app._studio_updates.render_pending
    assert bool(app.mask_overlay.get())
    assert app.undo_mask_btn.cget("state") == "disabled"
    assert app.redo_mask_btn.cget("state") == "disabled"
    assert app.tool_buttons["undo"].cget("state") == "disabled"
    assert app.tool_buttons["redo"].cget("state") == "disabled"

    # Project and Studio panels remain readable across the resize/HiDPI matrix.
    assert app.left_panel.winfo_width() >= 326, (
        f"Left sidebar is too narrow: {app.left_panel.winfo_width()}"
    )
    assert app.clear_btn.winfo_width() >= 80
    clear_parent = app.clear_btn.master
    assert (
        app.clear_btn.winfo_x() + app.clear_btn.winfo_width()
        <= clear_parent.winfo_width() + 2
    )
    assert app.right_panel.winfo_width() >= 420
    assert app.before_canvas.winfo_width() >= 120
    assert app.after_canvas.winfo_width() >= 120

    for label, widget in (
        ("left panel", app.left_panel),
        ("right panel", app.right_panel),
        ("before preview", app.before_canvas),
        ("after preview", app.after_canvas),
        ("language selector", app.lang),
        ("GitHub branding", app.footer_github),
    ):
        _assert_inside_root(root, widget, label=label)

    # 0.3.4 workflow is retained.
    assert app.studio_mode.get() == "cutout"
    assert len(app.studio_mode_bar.cget("values")) == 4
    assert not app._filmstrip_expanded
    app._toggle_filmstrip()
    root.update_idletasks()
    assert app._filmstrip_expanded
    _assert_inside_root(root, app.filmstrip_toggle, label="filmstrip toggle")
    app._toggle_filmstrip()
    root.update_idletasks()
    assert not app._filmstrip_expanded

    # Studio Pro inspector uses pages so controls do not need to be crushed.
    assert len(app.inspector_tabs.cget("values")) == 3

    app._show_inspector("ai")
    root.update_idletasks()
    ai_h, ai_bottom = _page_fits(app.ai_page, [app.ai_card, app.refine_card])
    assert ai_bottom <= ai_h, f"AI inspector clipped: {ai_bottom}>{ai_h}"
    _assert_inside_root(root, app.remove_btn, label="AI remove button")

    app._show_inspector("create")
    root.update_idletasks()
    create_h, create_bottom = _page_fits(
        app.create_page, [app.manual_card, app.subject_card, app.style_card]
    )
    assert create_bottom <= create_h, (
        f"Create inspector clipped: {create_bottom}>{create_h}"
    )
    _assert_inside_root(root, app.restore_btn, label="restore button")
    _assert_inside_root(root, app.erase_btn, label="erase button")
    _assert_inside_root(root, app.mask_overlay_switch, label="mask overlay switch")

    app._show_inspector("export")
    root.update_idletasks()
    export_h, export_bottom = _page_fits(
        app.export_page, [app.export_card, app.mask_export_card]
    )
    assert export_bottom <= export_h, (
        f"Export inspector clipped: {export_bottom}>{export_h}"
    )
    _assert_inside_root(root, app.export_btn, label="export button")
    _assert_inside_root(root, app.export_mask_btn, label="mask export button")

    # Creative controls are wired and usable.
    assert app.subject_scale.get() > 0
    assert app.outline_width.get() >= 1
    assert len(app.preview_selector.cget("values")) == 6
    assert app._preview_label("edge") in app.preview_selector.cget("values")
    assert app._preview_label("compare") in app.preview_selector.cget("values")
    assert 0 <= app.spill_strength.get() <= 100
    assert 0 <= app.wipe_position.get() <= 100
    assert app.export_mask_btn.winfo_height() >= 30

    # Compare mode swaps presets for the wipe control without growing the card.
    app._show_inspector("create")
    app._on_preview_mode(app._preview_label("compare"))
    root.update_idletasks()
    assert app.preview_mode.get() == "compare"
    assert app.wipe_frame.winfo_ismapped()
    assert not app.style_presets.winfo_ismapped()
    compare_h, compare_bottom = _page_fits(
        app.create_page, [app.manual_card, app.subject_card, app.style_card]
    )
    assert compare_bottom <= compare_h, (
        f"Compare inspector clipped: {compare_bottom}>{compare_h}"
    )
    _assert_inside_root(root, app.wipe_slider, label="compare wipe slider")
    app._on_preview_mode(app._preview_label("result"))
    root.update_idletasks()
    assert not app.wipe_frame.winfo_ismapped()
    assert app.style_presets.winfo_ismapped()

    # The manual editor overlay stays compact. With the overlay disabled the
    # editor prefers the real composed result, and plain pointer motion updates
    # only cursor primitives instead of rebuilding the full image preview.
    app.tool = "restore"
    app._after_transform = (0.0, 0.0, 1.0)
    app.preview_after = Image.new("RGBA", (8, 8), (20, 40, 60, 255))
    app.mask_overlay.set(False)
    assert app._after_image() is app.preview_after

    original_refresh = app._refresh_after_only

    def unexpected_refresh():
        raise AssertionError("Cursor-only motion must not rebuild the preview")

    app._refresh_after_only = unexpected_refresh
    try:
        event = type("PointerEvent", (), {"x": 60, "y": 60})()
        app._on_after_motion(event)
    finally:
        app._refresh_after_only = original_refresh

    cursor_items = app.after_canvas.find_withtag("cursor")
    assert len(cursor_items) >= 4
    app.after_canvas.delete("cursor")
    app._toggle_mask_overlay()
    assert bool(app.mask_overlay.get())

    for button in (
        app.remove_btn,
        app.restore_btn,
        app.erase_btn,
        app.undo_mask_btn,
        app.redo_mask_btn,
        app.export_btn,
        app.process_all_btn,
        app.export_mask_btn,
    ):
        assert button.winfo_width() >= 72
        assert button.winfo_height() >= 20

    readable_widgets = [
        app.files_project,
        app.add_images_btn,
        app.add_folder_btn,
        app.project_files,
        app.studio_modes_label,
        app.studio_mode_bar,
        app.pro_title,
        app.inspector_tabs,
        app.subject_title,
        app.style_title,
        app.spill_switch,
        app.spill_strength_label,
        app.wipe_label,
        app.wipe_value_label,
        app.mask_overlay_switch,
        app.undo_mask_btn,
        app.redo_mask_btn,
        app.export_title,
        app.status_label,
        app._diag_button,
        app.filmstrip_toggle,
    ]
    for widget in readable_widgets:
        assert _font_size(widget) >= 9, (
            f"Unreadably small font on {widget}: {_font_size(widget)}pt"
        )

    root.destroy()
    print(
        "BackgroundPXR Studio Pro smoke test passed "
        f"at {target_width}x{target_height} "
        f"(startup minimum {placement.min_width}x{placement.min_height})"
    )


if __name__ == "__main__":
    main()
