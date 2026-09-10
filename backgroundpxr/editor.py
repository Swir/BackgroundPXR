from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageFilter, ImageOps


@dataclass(slots=True)
class BrushSettings:
    size: int = 48
    hardness: int = 75


class MaskEditor:
    """Non-destructive alpha-mask editor for manual background cleanup."""

    def __init__(self, original: Image.Image, cutout: Image.Image, history_limit: int = 16) -> None:
        self.original = original.convert("RGBA")
        alpha = cutout.convert("RGBA").getchannel("A")
        if alpha.size != self.original.size:
            alpha = alpha.resize(self.original.size, Image.Resampling.LANCZOS)
        self.initial_alpha = alpha.copy()
        self.alpha = alpha.copy()
        self.history_limit = max(2, int(history_limit))
        self._undo: deque[Image.Image] = deque(maxlen=self.history_limit)
        self._redo: deque[Image.Image] = deque(maxlen=self.history_limit)
        self._stroke_saved = False

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def current_cutout(self) -> Image.Image:
        out = self.original.copy()
        out.putalpha(self.alpha)
        return out

    def begin_stroke(self) -> None:
        self._push_undo()
        self._stroke_saved = True

    def end_stroke(self) -> None:
        self._stroke_saved = False

    def _push_undo(self) -> None:
        self._undo.append(self.alpha.copy())
        self._redo.clear()

    @staticmethod
    def _brush_mask(size: int, hardness: int) -> Image.Image:
        from PIL import ImageDraw
        diameter = max(3, int(size))
        mask = Image.new("L", (diameter, diameter), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((1, 1, diameter - 2, diameter - 2), fill=255)
        hardness = max(0, min(100, int(hardness)))
        if hardness < 100:
            blur = max(0.35, diameter * (100 - hardness) / 100 * 0.18)
            mask = mask.filter(ImageFilter.GaussianBlur(blur))
        return mask

    def paint(self, x: float, y: float, mode: str, settings: BrushSettings) -> None:
        if not self._stroke_saved:
            self.begin_stroke()
        size = max(3, min(500, int(settings.size)))
        brush = self._brush_mask(size, settings.hardness)
        left = int(round(x - size / 2)); top = int(round(y - size / 2))
        right = left + size; bottom = top + size
        ix0, iy0 = max(0, left), max(0, top)
        ix1, iy1 = min(self.alpha.width, right), min(self.alpha.height, bottom)
        if ix1 <= ix0 or iy1 <= iy0:
            return
        bx0, by0 = ix0 - left, iy0 - top
        local_brush = brush.crop((bx0, by0, bx0 + ix1 - ix0, by0 + iy1 - iy0))
        local_alpha = self.alpha.crop((ix0, iy0, ix1, iy1))
        edited = ImageChops.screen(local_alpha, local_brush) if mode == "restore" else ImageChops.multiply(local_alpha, ImageOps.invert(local_brush))
        self.alpha.paste(edited, (ix0, iy0))

    def undo(self) -> bool:
        if not self._undo:
            return False
        self._redo.append(self.alpha.copy()); self.alpha = self._undo.pop(); return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        self._undo.append(self.alpha.copy()); self.alpha = self._redo.pop(); return True

    def reset(self) -> None:
        self._push_undo(); self.alpha = self.initial_alpha.copy()

    def smart_cleanup(self, strength: int = 35) -> None:
        self._push_undo(); strength = max(0, min(100, int(strength))); cutoff = 2 + round(strength * 0.42)
        alpha = self.alpha.filter(ImageFilter.MedianFilter(3))
        self.alpha = alpha.point(lambda p: 0 if p < cutoff else (255 if p > 250 - cutoff // 2 else p))

    def remove_small_islands(self, min_ratio: float = 0.003) -> int:
        self._push_undo(); max_side = 420; scale = min(1.0, max_side / max(self.alpha.size))
        sw, sh = max(1, round(self.alpha.width * scale)), max(1, round(self.alpha.height * scale))
        small = self.alpha.resize((sw, sh), Image.Resampling.BILINEAR); pix = small.load(); seen = bytearray(sw * sh); components = []
        for y in range(sh):
            for x in range(sw):
                idx = y * sw + x
                if seen[idx] or pix[x, y] < 40:
                    continue
                stack = [(x, y)]; seen[idx] = 1; comp = []
                while stack:
                    cx, cy = stack.pop(); comp.append((cx, cy))
                    for nx, ny in ((cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)):
                        if 0 <= nx < sw and 0 <= ny < sh:
                            nidx = ny * sw + nx
                            if not seen[nidx] and pix[nx, ny] >= 40:
                                seen[nidx] = 1; stack.append((nx, ny))
                components.append(comp)
        if not components:
            return 0
        largest = max(len(c) for c in components); threshold = max(12, round(largest * max(0.0005, min(0.1, min_ratio))))
        keep = Image.new("L", (sw, sh), 0); kp = keep.load(); removed = 0
        for comp in components:
            if len(comp) >= threshold:
                for x, y in comp:
                    kp[x, y] = 255
            else:
                removed += 1
        keep = keep.resize(self.alpha.size, Image.Resampling.NEAREST)
        self.alpha = ImageChops.multiply(self.alpha, keep)
        return removed
