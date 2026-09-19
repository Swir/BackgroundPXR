from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


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


def mask_overlay_image(
    cutout: Image.Image,
    kept_opacity: int = 52,
    removed_opacity: int = 92,
    fringe_opacity: int = 155,
) -> Image.Image:
    """Render a non-destructive manual-edit mask overlay.

    Kept pixels receive a restrained cyan tint, removed pixels a stronger
    magenta tint, and semi-transparent edge pixels an amber tint. The preview
    is always opaque so it remains readable over transparent areas, while the
    source ``cutout`` is never modified.
    """
    rgba = cutout.convert("RGBA")
    alpha = rgba.getchannel("A")

    kept_strength = max(0, min(255, int(kept_opacity)))
    removed_strength = max(0, min(255, int(removed_opacity)))
    fringe_strength = max(0, min(255, int(fringe_opacity)))

    preview = Image.new("RGBA", rgba.size, (24, 30, 39, 255))
    visible_subject = rgba.copy()
    visible_subject.putalpha(alpha)
    preview.alpha_composite(visible_subject)

    removed = ImageOps.invert(alpha).point(
        lambda p: (p * removed_strength) // 255
    )
    removed_overlay = Image.new("RGBA", rgba.size, (255, 66, 150, 255))
    removed_overlay.putalpha(removed)
    preview.alpha_composite(removed_overlay)

    kept = alpha.point(lambda p: (p * kept_strength) // 255)
    kept_overlay = Image.new("RGBA", rgba.size, (53, 207, 255, 255))
    kept_overlay.putalpha(kept)
    preview.alpha_composite(kept_overlay)

    fringe = alpha.point(
        lambda p: 0 if p in (0, 255) else min(255, 2 * min(p, 255 - p))
    )
    if fringe.getbbox() is not None and fringe_strength:
        fringe = fringe.point(lambda p: (p * fringe_strength) // 255)
        fringe_overlay = Image.new("RGBA", rgba.size, (255, 190, 52, 255))
        fringe_overlay.putalpha(fringe)
        preview.alpha_composite(fringe_overlay)

    return preview


def wipe_compare_image(
    before: Image.Image,
    after: Image.Image,
    position: float = 50.0,
    divider_width: int = 2,
) -> Image.Image:
    """Create a non-destructive before/after wipe comparison image.

    ``position`` is the percentage of the canvas occupied by the original image
    from the left. The processed result is shown on the right. When the source
    and result use different canvas sizes, the original is padded (never
    stretched) to the processed result size so the comparison stays predictable.
    """
    result = after.convert("RGBA")
    original = before.convert("RGBA")
    if original.size != result.size:
        original = ImageOps.pad(
            original,
            result.size,
            method=Image.Resampling.LANCZOS,
            color=(9, 24, 39, 255),
            centering=(0.5, 0.5),
        )

    pct = max(0.0, min(100.0, float(position)))
    split = int(round(result.width * pct / 100.0))
    preview = result.copy()
    if split > 0:
        preview.paste(original.crop((0, 0, split, result.height)), (0, 0))

    if 0 < split < result.width:
        half = max(1, int(divider_width)) // 2
        left = max(0, split - half)
        right = min(
            result.width - 1,
            split + max(1, int(divider_width)) - half - 1,
        )
        ImageDraw.Draw(preview).rectangle(
            (left, 0, right, result.height - 1), fill=(53, 207, 255, 255)
        )

    return preview
