"""Image processing utilities for ToolNest / MakeitDoc.

Provides robust operations for image editing using Pillow:
- Rotation, Flipping, Cropping, Resizing
- Color and tonal adjustments (Brightness, Contrast, Saturation, Sharpness)
- Text overlay with customizable positioning, font size, and color
- Format conversion and optimization (PNG, JPEG, WebP)
"""

from __future__ import annotations

import io
from typing import Tuple, Union, Optional
from PIL import Image, ImageEnhance, ImageOps, ImageDraw, ImageFont, UnidentifiedImageError
from PIL.Image import DecompressionBombError, DecompressionBombWarning
import warnings

# Safety limits
MAX_IMAGE_PIXELS = 25_000_000
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
ALLOWED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}

warnings.simplefilter("error", DecompressionBombWarning)
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class ImageProcessingError(Exception):
    """Custom exception raised for image manipulation errors."""
    pass


def open_image(file_or_bytes: Union[io.BytesIO, bytes, str]) -> Image.Image:
    """Open and validate an image file or byte stream.
    
    Ensures safe loading and converts color modes if necessary.
    """
    try:
        if isinstance(file_or_bytes, bytes):
            stream = io.BytesIO(file_or_bytes)
        elif isinstance(file_or_bytes, str):
            stream = file_or_bytes
        else:
            stream = file_or_bytes

        image = Image.open(stream)
        image.load()  # Force loading data to catch corrupt images early
        return image
    except (DecompressionBombError, DecompressionBombWarning) as exc:
        raise ImageProcessingError("Image dimensions exceed the allowed safety limit.") from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageProcessingError("Failed to open or decode image file.") from exc


def rotate_image(image: Image.Image, angle: int) -> Image.Image:
    """Rotate image by angle (in degrees clockwise or counterclockwise).
    
    Standard multiples of 90 are handled cleanly using transpose.
    """
    normalized_angle = angle % 360
    if normalized_angle == 0:
        return image.copy()
    elif normalized_angle == 90:
        return image.transpose(Image.Transpose.ROTATE_270)  # Clockwise 90
    elif normalized_angle == 180:
        return image.transpose(Image.Transpose.ROTATE_180)
    elif normalized_angle == 270:
        return image.transpose(Image.Transpose.ROTATE_90)   # Clockwise 270 / Counter-clockwise 90
    else:
        # Arbitrary rotation
        return image.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)


def flip_image(image: Image.Image, horizontal: bool = True, vertical: bool = False) -> Image.Image:
    """Flip an image horizontally, vertically, or both."""
    result = image.copy()
    if horizontal:
        result = result.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if vertical:
        result = result.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return result


def crop_image(
    image: Image.Image,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> Image.Image:
    """Crop image to bounding box (left, top, right, bottom)."""
    width, height = image.size

    left = max(0, min(left, width))
    top = max(0, min(top, height))
    right = max(0, min(right, width))
    bottom = max(0, min(bottom, height))

    if right <= left or bottom <= top:
        raise ImageProcessingError("Invalid crop area dimensions.")

    return image.crop((left, top, right, bottom))


def resize_image(
    image: Image.Image,
    target_width: int,
    target_height: int,
    maintain_aspect_ratio: bool = True,
) -> Image.Image:
    """Resize an image to target dimensions.
    
    If maintain_aspect_ratio is True, scales to fit within target_width and target_height.
    """
    if target_width <= 0 or target_height <= 0:
        raise ImageProcessingError("Width and height must be positive numbers.")

    if target_width * target_height > MAX_IMAGE_PIXELS:
        raise ImageProcessingError("Target dimensions exceed maximum allowed pixels.")

    if maintain_aspect_ratio:
        orig_w, orig_h = image.size
        ratio = min(target_width / orig_w, target_height / orig_h)
        new_w = max(1, int(round(orig_w * ratio)))
        new_h = max(1, int(round(orig_h * ratio)))
        return image.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
    else:
        return image.resize((target_width, target_height), resample=Image.Resampling.LANCZOS)


def adjust_image(
    image: Image.Image,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0,
) -> Image.Image:
    """Apply adjustments (1.0 = unchanged).
    
    Accepts floats:
    - brightness: 0.0 (black) to 2.0 (double)
    - contrast: 0.0 (gray) to 2.0 (high contrast)
    - saturation: 0.0 (black & white) to 2.0 (vivid)
    - sharpness: 0.0 (blurred) to 2.0 (sharp)
    """
    result = image.copy()

    # Convert to RGB if palette mode before enhancing
    if result.mode in ("P", "1"):
        result = result.convert("RGBA" if "transparency" in result.info else "RGB")

    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(result)
        result = enhancer.enhance(max(0.0, brightness))

    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(max(0.0, contrast))

    if saturation != 1.0:
        enhancer = ImageEnhance.Color(result)
        result = enhancer.enhance(max(0.0, saturation))

    if sharpness != 1.0:
        enhancer = ImageEnhance.Sharpness(result)
        result = enhancer.enhance(max(0.0, sharpness))

    return result


def add_text_to_image(
    image: Image.Image,
    text: str,
    position: Tuple[float, float] = (0.5, 0.5),  # (x_ratio, y_ratio) 0.0 to 1.0
    font_size: int = 36,
    text_color: str = "#ffffff",
    outline_color: Optional[str] = "#000000",
    outline_width: int = 2,
) -> Image.Image:
    """Render text onto image with optional outline/shadow for high visibility."""
    if not text.strip():
        return image.copy()

    # Create RGBA copy to support clean anti-aliased drawing
    working_image = image.convert("RGBA")
    draw = ImageDraw.Draw(working_image)

    # Attempt to load a default TrueType font or fallback to basic font
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.load_default(size=font_size)
        except TypeError:
            font = ImageFont.load_default()

    img_w, img_h = working_image.size

    # Calculate text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Calculate placement
    x = int(round(position[0] * img_w - text_w / 2))
    y = int(round(position[1] * img_h - text_h / 2))

    # Keep within visible boundaries
    x = max(10, min(x, img_w - text_w - 10))
    y = max(10, min(y, img_h - text_h - 10))

    # Draw outline/stroke if requested
    if outline_color and outline_width > 0:
        draw.text(
            (x, y),
            text,
            font=font,
            fill=text_color,
            stroke_width=outline_width,
            stroke_fill=outline_color,
        )
    else:
        draw.text((x, y), text, font=font, fill=text_color)

    # Convert back if original was not RGBA
    if image.mode != "RGBA":
        if image.mode == "RGB":
            return working_image.convert("RGB")
        elif image.mode == "L":
            return working_image.convert("L")
    return working_image


def export_image(
    image: Image.Image,
    output_format: str = "PNG",
    quality: int = 90,
) -> bytes:
    """Export PIL image to bytes in the requested format (PNG, JPEG, WEBP)."""
    fmt = output_format.upper().strip()
    if fmt == "JPG":
        fmt = "JPEG"

    if fmt not in {"PNG", "JPEG", "WEBP"}:
        raise ImageProcessingError(f"Unsupported format '{output_format}'.")

    buffer = io.BytesIO()

    to_save = image
    if fmt == "JPEG" and image.mode in ("RGBA", "LA", "P"):
        # JPEG does not support transparency; flatten onto white background
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            to_save = image.convert("RGBA")
        background.paste(to_save, mask=to_save.split()[-1] if to_save.mode == "RGBA" else None)
        to_save = background

    save_kwargs = {}
    if fmt in ("JPEG", "WEBP"):
        save_kwargs["quality"] = max(10, min(quality, 100))
        save_kwargs["optimize"] = True
    elif fmt == "PNG":
        save_kwargs["optimize"] = True

    to_save.save(buffer, format=fmt, **save_kwargs)
    buffer.seek(0)
    return buffer.getvalue()
