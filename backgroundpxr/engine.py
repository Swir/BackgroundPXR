from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from PIL import Image, ImageFilter, ImageOps

MODEL_MAP = {
    "Quality": "isnet-general-use",
    "Jakość": "isnet-general-use",
    "Fast": "u2netp",
    "Szybki": "u2netp",
    "Portrait": "birefnet-portrait",
    "Portret": "birefnet-portrait",
}

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

CANVAS_PRESETS = {
    "Original": None,
    "Oryginał": None,
    "Square 1:1": (1, 1),
    "Kwadrat 1:1": (1, 1),
    "Portrait 4:5": (4, 5),
    "Portret 4:5": (4, 5),
    "Story 9:16": (9, 16),
    "Relacja 9:16": (9, 16),
    "Landscape 16:9": (16, 9),
    "Poziomo 16:9": (16, 9),
    "Product 2000": (2000, 2000),
    "Produkt 2000": (2000, 2000),
}


@dataclass(slots=True)
class ProcessOptions:
    model_label: str = "Quality"
    background_mode: str = "transparent"
    background_color: str = "#FFFFFF"
    background_image: str | None = None
    background_blur: float = 18.0
    edge_softness: float = 0.0
    shadow: bool = False
    trim: bool = False
    padding: int = 24
    canvas_preset: str = "Original"
    export_format: str = "PNG"
    output_suffix: str = "_pxr"


class BackgroundEngine:
    def __init__(self) -> None:
        self._sessions: dict[str, object] = {}
        self._lock = Lock()

    def _get_session(self, model_label: str):
        model_name = MODEL_MAP.get(model_label, "isnet-general-use")
        with self._lock:
            if model_name not in self._sessions:
                try:
                    from rembg import new_session
                except ImportError as exc:
                    raise RuntimeError("Background removal engine is missing. Install requirements.txt") from exc
                self._sessions[model_name] = new_session(model_name)
            return self._sessions[model_name]

    def remove_background(self, image: Image.Image, model_label: str) -> Image.Image:
        try:
            from rembg import remove
        except ImportError as exc:
            raise RuntimeError("Background removal engine is missing. Install requirements.txt") from exc
        source = ImageOps.exif_transpose(image).convert("RGBA")
        result = remove(source, session=self._get_session(model_label))
        if not isinstance(result, Image.Image):
            raise RuntimeError("AI engine returned an unsupported result.")
        return result.convert("RGBA")

    @staticmethod
    def _soften_alpha(foreground: Image.Image, softness: float) -> Image.Image:
        if softness <= 0:
            return foreground
        alpha = foreground.getchannel("A").filter(ImageFilter.GaussianBlur(radius=max(0.1, min(8.0, float(softness)))))
        out = foreground.copy()
        out.putalpha(alpha)
        return out

    @staticmethod
    def _add_shadow(foreground: Image.Image) -> Image.Image:
        w, h = foreground.size
        blur = max(4, int(min(w, h) * 0.012))
        offset_x = max(4, int(w * 0.012))
        offset_y = max(6, int(h * 0.018))
        margin = blur * 3
        canvas = Image.new("RGBA", (w + margin * 2 + offset_x, h + margin * 2 + offset_y), (0, 0, 0, 0))
        alpha = foreground.getchannel("A")
        shadow_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=blur)).point(lambda p: int(p * 0.42))
        shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        shadow_layer.putalpha(shadow_alpha)
        canvas.alpha_composite(shadow_layer, (margin + offset_x, margin + offset_y))
        canvas.alpha_composite(foreground, (margin, margin))
        return canvas

    @staticmethod
    def _trim(foreground: Image.Image, padding: int) -> Image.Image:
        bbox = foreground.getchannel("A").getbbox()
        if not bbox:
            return foreground
        cropped = foreground.crop(bbox)
        pad = max(0, int(padding))
        canvas = Image.new("RGBA", (cropped.width + pad * 2, cropped.height + pad * 2), (0, 0, 0, 0))
        canvas.alpha_composite(cropped, (pad, pad))
        return canvas

    @staticmethod
    def _target_size(source_size: tuple[int, int], preset: str) -> tuple[int, int]:
        value = CANVAS_PRESETS.get(preset)
        if value is None:
            return source_size
        if value == (2000, 2000):
            return value
        rw, rh = value
        w, h = source_size
        base = max(w, h)
        if rw >= rh:
            return (base, max(1, round(base * rh / rw)))
        return (max(1, round(base * rw / rh)), base)

    @staticmethod
    def _place_subject(foreground: Image.Image, target: tuple[int, int]) -> Image.Image:
        if foreground.size == target:
            return foreground
        safe = (max(1, int(target[0] * 0.90)), max(1, int(target[1] * 0.90)))
        fitted = ImageOps.contain(foreground, safe, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", target, (0, 0, 0, 0))
        x = (target[0] - fitted.width) // 2
        y = (target[1] - fitted.height) // 2
        canvas.alpha_composite(fitted, (x, y))
        return canvas

    @staticmethod
    def _make_background(size: tuple[int, int], options: ProcessOptions, original: Image.Image) -> Image.Image:
        mode = options.background_mode
        if mode == "white":
            return Image.new("RGBA", size, (255, 255, 255, 255))
        if mode == "color":
            return Image.new("RGBA", size, options.background_color or "#FFFFFF")
        if mode == "image":
            if not options.background_image:
                raise RuntimeError("No replacement background image selected.")
            with Image.open(options.background_image) as bg_file:
                bg = ImageOps.exif_transpose(bg_file).convert("RGBA")
            return ImageOps.fit(bg, size, method=Image.Resampling.LANCZOS)
        if mode == "blur":
            bg = ImageOps.fit(original.convert("RGBA"), size, method=Image.Resampling.LANCZOS)
            radius = max(1.0, min(80.0, float(options.background_blur)))
            return bg.filter(ImageFilter.GaussianBlur(radius=radius))
        return Image.new("RGBA", size, (0, 0, 0, 0))

    def process(self, source_path: str | Path, options: ProcessOptions) -> Image.Image:
        with Image.open(source_path) as src:
            original = ImageOps.exif_transpose(src).convert("RGBA")
            cutout = self.remove_background(original, options.model_label)

        cutout = self._soften_alpha(cutout, options.edge_softness)
        if options.trim:
            cutout = self._trim(cutout, options.padding)
        if options.shadow:
            cutout = self._add_shadow(cutout)

        target = self._target_size(original.size if options.canvas_preset not in {"Original", "Oryginał"} else cutout.size, options.canvas_preset)
        subject = self._place_subject(cutout, target)
        if options.background_mode == "transparent":
            return subject

        background = self._make_background(target, options, original)
        background.alpha_composite(subject)
        return background

    @staticmethod
    def save(image: Image.Image, destination: str | Path, export_format: str) -> Path:
        fmt = export_format.upper()
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        if fmt in {"JPG", "JPEG"}:
            base = Image.new("RGB", image.size, "white")
            if image.mode == "RGBA":
                base.paste(image, mask=image.getchannel("A"))
            else:
                base.paste(image.convert("RGB"))
            base.save(path, "JPEG", quality=95, optimize=True)
        elif fmt == "WEBP":
            image.save(path, "WEBP", quality=96, method=6)
        else:
            image.save(path, "PNG", optimize=True)
        return path


def output_path_for(source: str | Path, output_dir: str | Path, export_format: str, suffix: str = "_pxr") -> Path:
    src = Path(source)
    ext = {"PNG": ".png", "JPG": ".jpg", "JPEG": ".jpg", "WEBP": ".webp"}.get(export_format.upper(), ".png")
    clean_suffix = suffix.strip() or "_pxr"
    clean_suffix = "".join(c for c in clean_suffix if c not in '<>:"/\\|?*')
    return Path(output_dir) / f"{src.stem}{clean_suffix}{ext}"


def collect_images(folder: str | Path) -> list[Path]:
    root = Path(folder)
    return sorted((p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS), key=lambda p: str(p).lower())


def is_supported_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
