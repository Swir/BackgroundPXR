from PIL import Image

from backgroundpxr.inspection import (
    edge_inspection_image,
    mask_overlay_image,
    wipe_compare_image,
)


def test_edge_inspection_marks_both_sides_of_alpha_boundary():
    cutout = Image.new("RGBA", (48, 48), (220, 30, 30, 0))
    alpha = Image.new("L", (48, 48), 0)
    alpha.paste(255, (12, 12, 36, 36))
    cutout.putalpha(alpha)

    preview = edge_inspection_image(cutout, edge_width=2)

    assert preview.mode == "RGBA"
    assert preview.size == cutout.size
    assert preview.getchannel("A").getextrema() == (255, 255)

    center = preview.getpixel((24, 24))
    outside_edge = preview.getpixel((10, 24))
    inside_edge = preview.getpixel((12, 24))

    assert center[:3] == (220, 30, 30)
    assert outside_edge[0] > outside_edge[1]
    assert outside_edge[2] > outside_edge[1]
    assert inside_edge[2] > inside_edge[0]


def test_edge_inspection_highlights_soft_fringe_without_mutating_source():
    cutout = Image.new("RGBA", (24, 24), (80, 120, 160, 0))
    alpha = Image.new("L", (24, 24), 0)
    alpha.paste(128, (6, 6, 18, 18))
    cutout.putalpha(alpha)
    before = cutout.tobytes()

    preview = edge_inspection_image(cutout)

    assert cutout.tobytes() == before
    fringe = preview.getpixel((12, 12))
    assert fringe[0] > fringe[2]
    assert fringe[1] > 80


def test_mask_overlay_distinguishes_kept_removed_and_soft_edge_pixels():
    cutout = Image.new("RGBA", (3, 1), (90, 100, 110, 255))
    cutout.putalpha(Image.new("L", (3, 1)))
    alpha = cutout.getchannel("A")
    alpha.putpixel((0, 0), 0)
    alpha.putpixel((1, 0), 128)
    alpha.putpixel((2, 0), 255)
    cutout.putalpha(alpha)

    preview = mask_overlay_image(cutout)

    removed = preview.getpixel((0, 0))
    fringe = preview.getpixel((1, 0))
    kept = preview.getpixel((2, 0))

    assert preview.getchannel("A").getextrema() == (255, 255)
    assert removed[0] > removed[1] and removed[2] > removed[1]
    assert fringe[0] > fringe[2] and fringe[1] > 80
    assert kept[2] > kept[0]


def test_mask_overlay_is_non_destructive_and_clamps_opacity_inputs():
    cutout = Image.new("RGBA", (8, 8), (40, 80, 120, 180))
    original = cutout.tobytes()

    preview = mask_overlay_image(
        cutout,
        kept_opacity=999,
        removed_opacity=-40,
        fringe_opacity=999,
    )

    assert cutout.tobytes() == original
    assert preview.mode == "RGBA"
    assert preview.size == cutout.size
    assert preview.getchannel("A").getextrema() == (255, 255)


def test_wipe_compare_splits_before_and_after_without_mutating_inputs():
    before = Image.new("RGBA", (20, 10), (240, 40, 30, 255))
    after = Image.new("RGBA", (20, 10), (20, 70, 220, 255))
    before_bytes = before.tobytes()
    after_bytes = after.tobytes()

    preview = wipe_compare_image(before, after, position=50, divider_width=2)

    assert preview.mode == "RGBA"
    assert preview.size == after.size
    assert preview.getpixel((2, 5)) == (240, 40, 30, 255)
    assert preview.getpixel((17, 5)) == (20, 70, 220, 255)
    assert preview.getpixel((10, 5)) == (53, 207, 255, 255)
    assert before.tobytes() == before_bytes
    assert after.tobytes() == after_bytes


def test_wipe_compare_clamps_position_and_pads_mismatched_source():
    before = Image.new("RGBA", (8, 16), (220, 180, 40, 255))
    after = Image.new("RGBA", (24, 12), (30, 40, 50, 255))

    all_after = wipe_compare_image(before, after, position=-25)
    all_before = wipe_compare_image(before, after, position=150)

    assert all_after.tobytes() == after.tobytes()
    assert all_before.size == after.size
    assert all_before.getpixel((12, 6))[:3] == (220, 180, 40)
