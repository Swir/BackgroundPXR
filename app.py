from __future__ import annotations

import os
import sys
import traceback
from importlib.metadata import version
from pathlib import Path

_FALLBACK_STREAMS = []


def ensure_writable_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and callable(getattr(stream, "write", None)):
            continue
        fallback = open(os.devnull, "w", encoding="utf-8", errors="replace")
        setattr(sys, name, fallback)
        _FALLBACK_STREAMS.append(fallback)


def functional_workflow_self_test() -> None:
    """Exercise the packaged non-AI Studio workflow without model/network access.

    The runtime import probe confirms that rembg/onnxruntime/pymatting are bundled.
    This deterministic companion probe verifies that the same frozen executable can
    also decode an image, carry a cutout through manual mask editing, render Studio
    composition and write every advertised export format plus a mask. It deliberately
    substitutes a synthetic AI mask so qualification never downloads a model.
    """
    from tempfile import TemporaryDirectory

    from PIL import Image, ImageDraw

    from backgroundpxr.editor import BrushSettings, MaskEditor
    from backgroundpxr.engine import BackgroundEngine, ProcessOptions

    class _ProbeEngine(BackgroundEngine):
        def remove_background(self, image: Image.Image, options: ProcessOptions) -> Image.Image:
            alpha = Image.new("L", image.size, 0)
            draw = ImageDraw.Draw(alpha)
            draw.rounded_rectangle((18, 8, 78, 64), radius=8, fill=255)
            out = image.convert("RGBA").copy()
            out.putalpha(alpha)
            return out

    with TemporaryDirectory(prefix="backgroundpxr-selftest-") as temp_dir:
        root = Path(temp_dir)
        source_path = root / "source.png"
        source = Image.new("RGBA", (96, 72), (48, 96, 160, 255))
        draw = ImageDraw.Draw(source)
        draw.ellipse((28, 12, 68, 58), fill=(240, 180, 70, 255))
        source.save(source_path, "PNG")

        engine = _ProbeEngine()
        base_options = ProcessOptions(
            alpha_matting=False,
            edge_softness=0.0,
            edge_contrast=0,
            background_mode="transparent",
        )
        layers = engine.process_layers(source_path, base_options)
        if layers.original.size != (96, 72) or layers.cutout.size != (96, 72):
            raise RuntimeError("Functional self-test failed: source/cutout geometry changed.")
        if layers.cutout.getchannel("A").getpixel((48, 36)) != 255:
            raise RuntimeError("Functional self-test failed: synthetic subject mask is missing.")
        if layers.cutout.getchannel("A").getpixel((2, 2)) != 0:
            raise RuntimeError("Functional self-test failed: synthetic background mask is opaque.")

        editor = MaskEditor(layers.original, layers.cutout, history_limit=6)
        brush = BrushSettings(size=14, hardness=100)
        editor.paint_segment(48, 36, 60, 36, "erase", brush)
        editor.end_stroke()
        erased = editor.alpha.getpixel((48, 36))
        if erased >= 255:
            raise RuntimeError("Functional self-test failed: erase brush did not change the mask.")
        if not editor.undo() or editor.alpha.getpixel((48, 36)) != 255:
            raise RuntimeError("Functional self-test failed: Undo did not restore the mask.")
        if not editor.redo() or editor.alpha.getpixel((48, 36)) >= 255:
            raise RuntimeError("Functional self-test failed: Redo did not restore the edit.")
        editor.paint_segment(48, 36, 60, 36, "restore", brush)
        editor.end_stroke()
        if editor.alpha.getpixel((48, 36)) != 255:
            raise RuntimeError("Functional self-test failed: restore brush did not recover the subject.")

        studio_options = ProcessOptions(
            background_mode="color",
            background_color="#123456",
            canvas_preset="Square 1:1",
            subject_scale=0.86,
            subject_offset_x=5.0,
            subject_offset_y=-4.0,
            outline=True,
            outline_width=3,
            outline_color="#FFFFFF",
            shadow=True,
            shadow_opacity=45,
            shadow_blur=3.0,
            shadow_offset_x=2,
            shadow_offset_y=3,
        )
        cutout = editor.current_cutout()
        output = engine.compose(layers.original, cutout, studio_options)
        if output.mode != "RGBA" or output.size != (96, 96):
            raise RuntimeError("Functional self-test failed: Studio composition geometry is invalid.")
        if output.getpixel((0, 0))[:3] != (18, 52, 86):
            raise RuntimeError("Functional self-test failed: replacement background was not composed.")

        exports = (("PNG", ".png"), ("JPG", ".jpg"), ("WEBP", ".webp"))
        for export_format, extension in exports:
            destination = root / f"workflow{extension}"
            engine.save(output, destination, export_format)
            if not destination.is_file() or destination.stat().st_size <= 0:
                raise RuntimeError(
                    f"Functional self-test failed: {export_format} export was not written."
                )
            with Image.open(destination) as saved:
                saved.load()
                if saved.size != output.size:
                    raise RuntimeError(
                        f"Functional self-test failed: {export_format} export geometry changed."
                    )

        mask_path = root / "workflow-mask.png"
        engine.save_mask(cutout, mask_path)
        with Image.open(mask_path) as mask:
            mask.load()
            if mask.mode != "L" or mask.size != cutout.size:
                raise RuntimeError("Functional self-test failed: mask export is invalid.")


def runtime_self_test() -> None:
    ensure_writable_stdio()
    assert sys.stdout is not None and callable(getattr(sys.stdout, "write", None))
    assert sys.stderr is not None and callable(getattr(sys.stderr, "write", None))

    import onnxruntime  # noqa: F401
    import pymatting  # noqa: F401
    import rembg  # noqa: F401
    from tqdm import tqdm

    version("pymatting")
    version("rembg")
    version("onnxruntime")

    probe = tqdm(total=1, file=sys.stderr, leave=False, desc="PXR runtime")
    probe.update(1)
    probe.close()

    functional_workflow_self_test()


def main() -> None:
    ensure_writable_stdio()

    if "--self-test-runtime" in sys.argv:
        report = Path.cwd() / "backgroundpxr_runtime_selftest.txt"
        try:
            runtime_self_test()
            report.write_text("OK\n", encoding="utf-8")
            return
        except Exception:
            report.write_text(traceback.format_exc(), encoding="utf-8")
            raise SystemExit(23)

    # DPI awareness must be selected before Tk creates the first native
    # window; otherwise Windows can bitmap-scale the UI and clip controls.
    from backgroundpxr.display import enable_windows_dpi_awareness

    enable_windows_dpi_awareness()

    from backgroundpxr.studio_v051 import BackgroundPXRStudio051App
    from backgroundpxr.ui import create_root

    root = create_root()
    BackgroundPXRStudio051App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
