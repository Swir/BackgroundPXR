from PIL import Image, ImageDraw

from backgroundpxr.editor import BrushSettings, MaskEditor


def make_editor():
    original = Image.new("RGBA", (100, 100), (120, 80, 40, 255))
    alpha = Image.new("L", (100, 100), 0)
    ImageDraw.Draw(alpha).rectangle((25, 25, 75, 75), fill=255)
    cut = original.copy(); cut.putalpha(alpha)
    return MaskEditor(original, cut)


def test_erase_restore_and_undo_redo():
    ed = make_editor(); ed.begin_stroke(); ed.paint(50, 50, "erase", BrushSettings(24, 100)); ed.end_stroke()
    assert ed.alpha.getpixel((50, 50)) == 0
    assert ed.undo(); assert ed.alpha.getpixel((50, 50)) == 255
    assert ed.redo(); assert ed.alpha.getpixel((50, 50)) == 0
    ed.begin_stroke(); ed.paint(50, 50, "restore", BrushSettings(24, 100)); ed.end_stroke()
    assert ed.alpha.getpixel((50, 50)) > 240


def test_reset_mask():
    ed = make_editor(); ed.begin_stroke(); ed.paint(50, 50, "erase", BrushSettings(30, 100)); ed.end_stroke(); ed.reset()
    assert ed.alpha.getpixel((50, 50)) == 255


def test_remove_small_island():
    original = Image.new("RGBA", (120, 120), (1, 2, 3, 255))
    alpha = Image.new("L", (120, 120), 0); d = ImageDraw.Draw(alpha)
    d.rectangle((20, 20, 95, 100), fill=255); d.rectangle((3, 3, 5, 5), fill=255)
    cut = original.copy(); cut.putalpha(alpha); ed = MaskEditor(original, cut)
    removed = ed.remove_small_islands(.01)
    assert removed >= 1
    assert ed.alpha.getpixel((4, 4)) == 0
    assert ed.alpha.getpixel((50, 50)) == 255
