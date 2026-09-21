from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

MODEL_MAP = {
    "High Quality v2": "birefnet-general",
    "Najwyższa jakość v2": "birefnet-general",
    "Quality": "isnet-general-use", "Jakość": "isnet-general-use",
    "Fast": "u2netp", "Szybki": "u2netp",
    "Portrait": "birefnet-portrait", "Portret": "birefnet-portrait",
}
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
CANVAS_PRESETS = {
    "Original": None, "Oryginał": None, "Original Size": None, "Oryginalny rozmiar": None,
    "Square 1:1": (1, 1), "Kwadrat 1:1": (1, 1),
    "Portrait 4:5": (4, 5), "Portret 4:5": (4, 5),
    "Story 9:16": (9, 16), "Relacja 9:16": (9, 16),
    "Landscape 16:9": (16, 9), "Poziomo 16:9": (16, 9),
    "Product 2000": (2000, 2000), "Produkt 2000": (2000, 2000),
    "Product 2000×2000": (2000, 2000), "Produkt 2000×2000": (2000, 2000),
}
BACKGROUND_CACHE_LIMIT = 4
ALPHA_MATTING_MAX_PIXELS = 4_000_000


@dataclass(slots=True)
class ProcessOptions:
    model_label: str = "High Quality v2"
    background_mode: str = "transparent"
    background_color: str = "#FFFFFF"
    background_image: str | None = None
    background_blur: float = 18.0
    edge_refine: int = 0
    edge_softness: float = 0.4
    edge_contrast: int = 8
    alpha_matting: bool = True
    shadow: bool = False
    trim: bool = False
    padding: int = 24
    canvas_preset: str = "Original"
    export_format: str = "PNG"
    output_suffix: str = "_pxr"

    # Studio Pro controls. They work on an already computed mask, so changing
    # them never needs another AI inference.
    subject_scale: float = 1.0
    subject_offset_x: float = 0.0
    subject_offset_y: float = 0.0
    outline: bool = False
    outline_width: int = 6
    outline_color: str = "#FFFFFF"
    shadow_opacity: int = 38
    shadow_blur: float = 18.0
    shadow_offset_x: int = 12
    shadow_offset_y: int = 18
    spill_cleanup: bool = False
    spill_strength: int = 55


@dataclass(slots=True)
class ProcessResult:
    original: Image.Image
    cutout: Image.Image
    output: Image.Image


class BackgroundEngine:
    def __init__(self) -> None:
        self._sessions: dict[str, object] = {}
        self._lock = Lock()
        self._background_cache_lock = Lock()
        self._background_cache: OrderedDict[tuple[object, ...], Image.Image] = OrderedDict()
        self.last_remove_notice: str | None = None
        self.last_remove_used_alpha_matting = False

    @staticmethod
    def _runtime_import_error(exc: BaseException) -> RuntimeError:
        package = getattr(exc, "name", None) or type(exc).__name__
        return RuntimeError(
            f"AI runtime failed to load ({package}): {exc}. "
            "The Windows build may be incomplete; open LOG and include this report when reporting the problem."
        )

    def _get_session(self, model_label: str):
        model_name = MODEL_MAP.get(model_label, "birefnet-general")
        with self._lock:
            if model_name not in self._sessions:
                try:
                    from rembg import new_session
                except ImportError as exc:
                    raise self._runtime_import_error(exc) from exc
                self._sessions[model_name] = new_session(model_name)
            return self._sessions[model_name]

    @staticmethod
    def _alpha_matting_work_image(source: Image.Image) -> tuple[Image.Image, bool]:
        """Return a bounded working image for memory-intensive closed-form matting.

        rembg's alpha-matting stage runs at the supplied image resolution and
        pymatting can allocate several large sparse-matrix buffers. Multi-megapixel
        originals can therefore require gigabytes of contiguous RAM even though the
        segmentation model itself is happy. Keep the expensive matting stage bounded
        while restoring the resulting alpha mask to the original output resolution.
        """
        pixels = max(1, source.width * source.height)
        if pixels <= ALPHA_MATTING_MAX_PIXELS:
            return source, False

        scale = (ALPHA_MATTING_MAX_PIXELS / pixels) ** 0.5
        width = max(1, round(source.width * scale))
        height = max(1, round(source.height * scale))
        return source.resize((width, height), Image.Resampling.LANCZOS), True

    @staticmethod
    def _restore_alpha_resolution(source: Image.Image, cutout: Image.Image) -> Image.Image:
        rgba = cutout.convert("RGBA")
        if rgba.size == source.size:
            return rgba

        alpha = rgba.getchannel("A").resize(source.size, Image.Resampling.LANCZOS)
        restored = source.copy()
        restored.putalpha(alpha)
        return restored

    def remove_background(self, image: Image.Image, options: ProcessOptions) -> Image.Image:
        try:
            from rembg import remove
        except ImportError as exc:
            raise self._runtime_import_error(exc) from exc

        source = ImageOps.exif_transpose(image).convert("RGBA")
        session = self._get_session(options.model_label)
        base_kwargs = dict(session=session, post_process_mask=True)
        self.last_remove_notice = None
        self.last_remove_used_alpha_matting = False

        if not options.alpha_matting:
            try:
                result = remove(source, **base_kwargs)
            except TypeError:
                result = remove(source, session=session)
        else:
            work_source, reduced_for_memory = self._alpha_matting_work_image(source)
            alpha_kwargs = dict(
                session=session,
                post_process_mask=True,
                alpha_matting=True,
                alpha_matting_foreground_threshold=245,
                alpha_matting_background_threshold=8,
                alpha_matting_erode_size=8,
            )
            try:
                result = remove(work_source, **alpha_kwargs)
                self.last_remove_used_alpha_matting = True
                if reduced_for_memory:
                    self.last_remove_notice = (
                        "Alpha matting used a memory-safe working resolution "
                        f"{work_source.width}x{work_source.height} for the "
                        f"{source.width}x{source.height} source; the final mask "
                        "was restored to the original resolution."
                    )
            except MemoryError:
                # pymatting can request multi-gigabyte contiguous arrays. Once
                # that happens, retry the reliable mask path rather than failing
                # the whole image/run. The segmentation session is reused.
                import gc

                gc.collect()
                self.last_remove_used_alpha_matting = False
                self.last_remove_notice = (
                    "Alpha matting exceeded available memory and was automatically "
                    "disabled for this image. AI removal was retried with the "
                    "memory-safe mask path at the original resolution."
                )
                try:
                    result = remove(source, **base_kwargs)
                except TypeError:
                    result = remove(source, session=session)
            except TypeError:
                # Preserve compatibility with rembg builds that do not expose the
                # alpha-matting keyword set expected by this release.
                self.last_remove_used_alpha_matting = False
                self.last_remove_notice = (
                    "The bundled AI runtime did not accept alpha-matting options, "
                    "so this image used the standard memory-safe mask path."
                )
                result = remove(source, session=session)

        if not isinstance(result, Image.Image):
            raise RuntimeError("AI engine returned an unsupported result.")

        if self.last_remove_used_alpha_matting and result.size != source.size:
            result = self._restore_alpha_resolution(source, result)
        return result.convert("RGBA")

    @staticmethod
    def _refine_alpha(alpha: Image.Image, options: ProcessOptions) -> Image.Image:
        refine = max(-7, min(7, int(options.edge_refine)))
        if refine:
            kernel = min(15, max(3, abs(refine) * 2 + 1))
            if kernel % 2 == 0:
                kernel += 1
            alpha = alpha.filter(
                ImageFilter.MaxFilter(kernel) if refine > 0 else ImageFilter.MinFilter(kernel)
            )
        if options.edge_softness > 0:
            alpha = alpha.filter(
                ImageFilter.GaussianBlur(max(0.05, min(5.0, float(options.edge_softness))))
            )
        contrast = max(-80, min(100, int(options.edge_contrast)))
        if contrast:
            factor = 1.0 + contrast / 100.0
            alpha = alpha.point(
                lambda p: max(0, min(255, round((p - 128) * factor + 128)))
            )
        return alpha

    def refine_cutout(
        self, original: Image.Image, ai_cutout: Image.Image, options: ProcessOptions
    ) -> Image.Image:
        alpha = self._refine_alpha(ai_cutout.getchannel("A"), options)
        out = original.convert("RGBA").copy()
        out.putalpha(alpha)
        if options.spill_cleanup and options.spill_strength > 0:
            out = self._decontaminate_color_spill(out, options.spill_strength)
        return out

    @staticmethod
    def _decontaminate_color_spill(cutout: Image.Image, strength: int = 55) -> Image.Image:
        """Reduce dominant color contamination on semi-transparent mask edges.

        This is intentionally generic: it detects the dominant RGB channel only
        on the alpha transition band and pulls that channel toward the stronger
        of the other two channels. It is useful for green/blue screen spill and
        colored background halos without changing solid interior pixels.
        """
        rgba = cutout.convert("RGBA")
        strength = max(0, min(100, int(strength)))
        if strength == 0:
            return rgba

        alpha = rgba.getchannel("A")
        expanded = alpha.filter(ImageFilter.MaxFilter(5))
        eroded = alpha.filter(ImageFilter.MinFilter(5))
        edge = ImageChops.subtract(expanded, eroded)
        if edge.getbbox() is None:
            return rgba

        rgb = rgba.convert("RGB")
        means = ImageStat.Stat(rgb, mask=edge).mean
        dominant = max(range(3), key=lambda i: means[i])
        others = [i for i in range(3) if i != dominant]
        if means[dominant] - max(means[i] for i in others) < 6.0:
            return rgba

        channels = list(rgb.split())
        target = ImageChops.lighter(channels[others[0]], channels[others[1]])
        excess = ImageChops.subtract(channels[dominant], target)
        edge_strength = edge.point(lambda p: round(p * strength / 100.0))
        reduction = ImageChops.multiply(excess, edge_strength)
        channels[dominant] = ImageChops.subtract(channels[dominant], reduction)

        cleaned = Image.merge("RGB", channels).convert("RGBA")
        cleaned.putalpha(alpha)
        return cleaned

    @staticmethod
    def _trim(fg: Image.Image, padding: int) -> Image.Image:
        bbox = fg.getchannel("A").getbbox()
        if not bbox:
            return fg
        crop = fg.crop(bbox)
        p = max(0, int(padding))
        out = Image.new("RGBA", (crop.width + p * 2, crop.height + p * 2), (0, 0, 0, 0))
        out.alpha_composite(crop, (p, p))
        return out

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
        return (
            (base, max(1, round(base * rh / rw)))
            if rw >= rh
            else (max(1, round(base * rw / rh)), base)
        )

    @staticmethod
    def _place_subject(
        fg: Image.Image,
        target: tuple[int, int],
        scale: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> Image.Image:
        """Place subject on a target canvas with user-controlled scale/position.

        scale=1.0 preserves the historical ~92% fit. Offsets are percentages of
        the target canvas, so +10 moves the subject 10% of the canvas width/right.
        """
        tw, th = target
        fw, fh = fg.size
        if fw <= 0 or fh <= 0:
            return Image.new("RGBA", target, (0, 0, 0, 0))

        # Preserve the exact 0.3.x behaviour for an untouched Original canvas.
        if (
            fg.size == target
            and abs(float(scale) - 1.0) < 1e-9
            and abs(float(offset_x)) < 1e-9
            and abs(float(offset_y)) < 1e-9
        ):
            return fg.copy()

        scale = max(0.20, min(1.80, float(scale)))
        fit = min(tw / fw, th / fh) * 0.92 * scale
        nw = max(1, round(fw * fit))
        nh = max(1, round(fh * fit))
        resized = fg.resize((nw, nh), Image.Resampling.LANCZOS)

        ox = round((tw - nw) / 2 + tw * max(-100.0, min(100.0, float(offset_x))) / 100.0)
        oy = round((th - nh) / 2 + th * max(-100.0, min(100.0, float(offset_y))) / 100.0)

        out = Image.new("RGBA", target, (0, 0, 0, 0))
        out.alpha_composite(resized, (ox, oy))
        return out

    @staticmethod
    def _outline_layer(subject: Image.Image, width: int, color: str) -> Image.Image:
        width = max(1, min(20, int(width)))
        kernel = width * 2 + 1
        alpha = subject.getchannel("A")
        expanded = alpha.filter(ImageFilter.MaxFilter(kernel))
        border = ImageChops.subtract(expanded, alpha)
        layer = Image.new("RGBA", subject.size, color or "#FFFFFF")
        layer.putalpha(border)
        return layer

    @staticmethod
    def _shadow_layer(
        subject: Image.Image,
        opacity: int,
        blur: float,
        offset_x: int,
        offset_y: int,
    ) -> Image.Image:
        opacity = max(0, min(100, int(opacity)))
        blur = max(0.0, min(80.0, float(blur)))
        alpha = subject.getchannel("A")
        if blur:
            alpha = alpha.filter(ImageFilter.GaussianBlur(blur))
        alpha = alpha.point(lambda p: round(p * opacity / 100.0))

        shifted = Image.new("L", subject.size, 0)
        shifted.paste(alpha, (int(offset_x), int(offset_y)))
        layer = Image.new("RGBA", subject.size, (0, 0, 0, 255))
        layer.putalpha(shifted)
        return layer

    @staticmethod
    def mask_image(cutout: Image.Image, invert: bool = False) -> Image.Image:
        mask = cutout.convert("RGBA").getchannel("A")
        return ImageOps.invert(mask) if invert else mask

    def clear_background_cache(self) -> None:
        """Drop prepared replacement/blur backgrounds held for Studio preview."""
        with self._background_cache_lock:
            self._background_cache.clear()

    def _background_cache_key(
        self,
        size: tuple[int, int],
        options: ProcessOptions,
        original: Image.Image,
    ) -> tuple[object, ...] | None:
        mode = options.background_mode
        if mode == "image":
            if not options.background_image:
                return None
            path = Path(options.background_image).expanduser()
            try:
                stat = path.stat()
                stamp = (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)
            except OSError:
                stamp = (None, None, None)
            return ("image", size, str(path.absolute()), *stamp)
        if mode == "blur":
            blur = max(1.0, min(80.0, float(options.background_blur)))
            # The editor keeps original immutable for the lifetime of a project.
            # Object identity therefore avoids hashing multi-megapixel images on
            # every slider frame while remaining source-specific.
            return (
                "blur",
                size,
                id(original),
                original.size,
                original.mode,
                round(blur, 3),
            )
        return None

    def _cached_background(self, key: tuple[object, ...]) -> Image.Image | None:
        with self._background_cache_lock:
            cached = self._background_cache.pop(key, None)
            if cached is None:
                return None
            self._background_cache[key] = cached
            return cached.copy()

    def _store_background(
        self, key: tuple[object, ...], background: Image.Image
    ) -> None:
        with self._background_cache_lock:
            self._background_cache.pop(key, None)
            self._background_cache[key] = background.copy()
            while len(self._background_cache) > BACKGROUND_CACHE_LIMIT:
                self._background_cache.popitem(last=False)

    @staticmethod
    def _render_background(
        size: tuple[int, int], options: ProcessOptions, original: Image.Image
    ) -> Image.Image:
        if options.background_mode == "white":
            return Image.new("RGBA", size, (255, 255, 255, 255))
        if options.background_mode == "color":
            return Image.new("RGBA", size, options.background_color or "#FFFFFF")
        if options.background_mode == "image":
            if not options.background_image:
                raise RuntimeError("No replacement background image selected.")
            with Image.open(options.background_image) as f:
                bg = ImageOps.exif_transpose(f).convert("RGBA")
            return ImageOps.fit(bg, size, method=Image.Resampling.LANCZOS)
        if options.background_mode == "blur":
            bg = ImageOps.fit(original.convert("RGBA"), size, method=Image.Resampling.LANCZOS)
            return bg.filter(
                ImageFilter.GaussianBlur(max(1, min(80, float(options.background_blur))))
            )
        return Image.new("RGBA", size, (0, 0, 0, 0))

    def _make_background(
        self, size: tuple[int, int], options: ProcessOptions, original: Image.Image
    ) -> Image.Image:
        key = self._background_cache_key(size, options, original)
        if key is not None:
            cached = self._cached_background(key)
            if cached is not None:
                return cached

        background = self._render_background(size, options, original)
        if key is not None:
            self._store_background(key, background)
            return background.copy()
        return background

    def compose(
        self, original: Image.Image, cutout: Image.Image, options: ProcessOptions
    ) -> Image.Image:
        subject = cutout.convert("RGBA")
        if options.trim:
            subject = self._trim(subject, options.padding)

        original_canvas = options.canvas_preset in {
            "Original", "Oryginał", "Original Size", "Oryginalny rozmiar"
        }
        source_size = subject.size if original_canvas else original.size
        target = self._target_size(source_size, options.canvas_preset)

        placed = self._place_subject(
            subject,
            target,
            options.subject_scale,
            options.subject_offset_x,
            options.subject_offset_y,
        )

        styled = Image.new("RGBA", target, (0, 0, 0, 0))
        if options.shadow:
            styled.alpha_composite(
                self._shadow_layer(
                    placed,
                    options.shadow_opacity,
                    options.shadow_blur,
                    options.shadow_offset_x,
                    options.shadow_offset_y,
                )
            )
        if options.outline and options.outline_width > 0:
            styled.alpha_composite(
                self._outline_layer(placed, options.outline_width, options.outline_color)
            )
        styled.alpha_composite(placed)

        if options.background_mode == "transparent":
            return styled

        bg = self._make_background(target, options, original)
        bg.alpha_composite(styled)
        return bg

    def process_layers(self, source_path: str | Path, options: ProcessOptions) -> ProcessResult:
        with Image.open(source_path) as src:
            original = ImageOps.exif_transpose(src).convert("RGBA")
        ai = self.remove_background(original, options)
        cutout = self.refine_cutout(original, ai, options)
        return ProcessResult(original, cutout, self.compose(original, cutout, options))

    def process(self, source_path: str | Path, options: ProcessOptions) -> Image.Image:
        return self.process_layers(source_path, options).output

    @staticmethod
    def save(image: Image.Image, destination: str | Path, export_format: str) -> Path:
        fmt = export_format.upper()
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        if fmt in {"JPG", "JPEG"}:
            base = Image.new("RGB", image.size, "white")
            base.paste(image, mask=image.getchannel("A") if image.mode == "RGBA" else None)
            base.save(path, "JPEG", quality=96, optimize=True)
        elif fmt == "WEBP":
            image.save(path, "WEBP", quality=97, method=6)
        else:
            image.save(path, "PNG", optimize=True)
        return path

    @staticmethod
    def save_mask(cutout: Image.Image, destination: str | Path, invert: bool = False) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        BackgroundEngine.mask_image(cutout, invert=invert).save(path, "PNG", optimize=True)
        return path


def output_path_for(
    source: str | Path,
    output_dir: str | Path,
    export_format: str,
    suffix: str = "_pxr",
) -> Path:
    src = Path(source)
    ext = {
        "PNG": ".png", "JPG": ".jpg", "JPEG": ".jpg", "WEBP": ".webp"
    }.get(export_format.upper(), ".png")
    clean = suffix.strip() or "_pxr"
    clean = "".join(c for c in clean if c not in '<>:"/\\|?*')
    return Path(output_dir) / f"{src.stem}{clean}{ext}"


def collect_images(folder: str | Path) -> list[Path]:
    root = Path(folder)
    return sorted(
        (
            p for p in root.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ),
        key=lambda p: str(p).lower(),
    )


def is_supported_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
