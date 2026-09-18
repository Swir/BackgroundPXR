from PIL import Image

from backgroundpxr.inspection import edge_inspection_image


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
