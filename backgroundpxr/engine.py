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


@dataclass(slots=True)
class ProcessOptions:
    model_label: str = "Quality"
    background_mode: str = "transparent"
    background_color: str = "#FFFFFF"
    background_image: str | None = None
    edge_softness: float = 0.0
    shadow: bool = False
    trim: bool = False
    padding: int = 24
    export_format: str = "PNG"


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
                    raise RuntimeError(
                        "Background removal engine is missing. Install dependencies with: pip install -r requirements.txt"
                    ) from exc
                self._sessions[model_name] = new_session(model_name)
            return self._sessions[model_name]

    def remove_background(self, image: Image.Image, model_label: str) -> Image.Image:
        try:
            from rembg import remove
        except ImportError as exc:
            raise RuntimeError(
                "Background removal engine is missing. Install dependencies with: pip install -r requirements.txt"
            ) from exc

        source = ImageOps.exif_transpose(image).convert("RGBA")
        session = self._get_session(model_label)
        result = remove(source, session=session)
        if not isinstance(result, Image.Image):
            raise RuntimeError("AI engine returned an unsupported result.")
        return result.convert("RGBA")

    @staticmethod
    def _soften_alpha(foreground: Image.Image, softness: float) -> Image.Image:
        if softness <= 0:
            return foreground
        alpha = foreground.getchannel("A")
        radius = max(0.1, min(8.0, float(softness)))
        alpha = alpha.filter(ImageFilter.GaussianBlur(radius=radius))
        output = foreground.copy()
        output.putalpha(alpha)
        return output

    @staticmethod
    def _add_shadow(foreground: Image.Image) -> Image.Image:
        w, h = foreground.size
        blur = max(4, int(min(w, h) * 0.012))
        offset_x = max(4, int(w * 0.012))
        offset_y = max(6, int(h * 0.018))
        margin = blur * 3
        canvas = Image.new(
            "RGBA",
            (w + margin * 2 + offset_x, h + margin * 2 + offset_y),
            (0, 0, 0, 0),
        )
        alpha = foreground.getchannel("A")
        shadow_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=blur))
        shadow_alpha = shadow_alpha.point(lambda p: int(p * 0.42))
        shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        shadow_layer.putalpha(shadow_alpha)
        canvas.alpha_composite(shadow_layer, (margin + offset_x, margin + offset_y))
        canvas.alpha_composite(foreground, (margin, margin))
        return canvas

    @staticmethod
    def _trim(foreground: Image.Image, padding: int) -> Image.Image:
        alpha = foreground.getchannel("A")
        bbox = alpha.getbbox()
        if not bbox:
            return foreground
        cropped = foreground.crop(bbox)
        pad = max(0, int(padding))
        if pad == 0:
            return cropped
        canvas = Image.new("RGBA", (cropped.width + pad * 2, cropped.height + pad * 2), (0, 0, 0, 0))
        canvas.alpha_composite(cropped, (pad, pad))
        return canvas

    @staticmethod
    def _make_background(size: tuple[int, int], options: ProcessOptions) -> Image.Image:
        mode = options.background_mode
        if mode == "white":
            return Image.new("RGBA", size, (255, 255, 255, 255))
        if mode == "color":
            color = options.background_color or "#FFFFFF"
            return Image.new("RGBA", size, color)
        if mode == "image":
            if not options.background_image:
                raise RuntimeError("No replacement background image selected.")
            with Image.open(options.background_image) as bg_file:
                bg = ImageOps.exif_transpose(bg_file).convert("RGBA")
            return ImageOps.fit(bg, size, method=Image.Resampling.LANCZOS)
        return Image.new("RGBA", size, (0, 0, 0, 0))

    def process(self, source_path: str | Path, options: ProcessOptions) -> Image.Image:
        with Image.open(source_path) as src:
            cutout = self.remove_background(src, options.model_label)

        cutout = self._soften_alpha(cutout, options.edge_softness)
        if options.trim:
            cutout = self._trim(cutout, options.padding)
        if options.shadow:
            cutout = self._add_shadow(cutout)

        if options.background_mode == "transparent":
            return cutout

        background = self._make_background(cutout.size, options)
        background.alpha_composite(cutout)
        return background

    @staticmethod
    def save(image: Image.Image, destination: str | Path, export_format: str) -> Path:
        fmt = export_format.upper()
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)

        if fmt in {"JPG", "JPEG"}:
            if image.mode == "RGBA":
                base = Image.new("RGB", image.size, "white")
                base.paste(image, mask=image.getchannel("A"))
                image = base
            else:
                image = image.convert("RGB")
            image.save(path, "JPEG", quality=95, optimize=True)
        elif fmt == "WEBP":
            image.save(path, "WEBP", quality=96, method=6)
        else:
            image.save(path, "PNG", optimize=True)
        return path


def output_path_for(source: str | Path, output_dir: str | Path, export_format: str) -> Path:
    src = Path(source)
    ext = {"PNG": ".png", "JPG": ".jpg", "JPEG": ".jpg", "WEBP": ".webp"}.get(export_format.upper(), ".png")
    return Path(output_dir) / f"{src.stem}_pxr{ext}"


def collect_images(folder: str | Path) -> list[Path]:
    root = Path(folder)
    return sorted(
        (p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS),
        key=lambda p: str(p).lower(),
    )


def is_supported_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
