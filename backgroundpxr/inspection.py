from __future__ import annotations

from PIL import Image, ImageChops, ImageFilter


def edge_inspection_image(cutout: Image.Image, edge_width: int = 2) -> Image.Image:
    """Render a high-contrast QA preview for inspecting alpha-mask boundaries.

    The subject is composited over a neutral dark matte while the mask boundary
    is marked on both sides: magenta outside the subject and cyan inside it.
    Semi-transparent fringe pixels receive an amber overlay, making halos,
    accidental cut-ins, and soft hair/fur transitions easier to spot without
    modifying the actual mask or export output.
    """
    rgba = cutout.convert("RGBA")
    alpha = rgba.getchannel("A")
    width = max(1, min(8, int(edge_width)))
    kernel = width * 2 + 1

    expanded = alpha.filter(ImageFilter.MaxFilter(kernel))
    eroded = alpha.filter(ImageFilter.MinFilter(kernel))
    outside = ImageChops.subtract(expanded, alpha)
    inside = ImageChops.subtract(alpha, eroded)
    fringe = alpha.point(
        lambda p: 0 if p in (0, 255) else min(255, 2 * min(p, 255 - p))
    )

    preview = Image.new("RGBA", rgba.size, (31, 36, 44, 255))
    preview.alpha_composite(rgba)

    outside_overlay = Image.new("RGBA", rgba.size, (255, 56, 154, 255))
    outside_overlay.putalpha(outside.point(lambda p: min(230, p)))
    preview.alpha_composite(outside_overlay)

    inside_overlay = Image.new("RGBA", rgba.size, (0, 224, 255, 255))
    inside_overlay.putalpha(inside.point(lambda p: min(210, p)))
    preview.alpha_composite(inside_overlay)

    if fringe.getbbox() is not None:
        fringe_overlay = Image.new("RGBA", rgba.size, (255, 190, 52, 255))
        fringe_overlay.putalpha(fringe.point(lambda p: min(180, p)))
        preview.alpha_composite(fringe_overlay)

    return preview
