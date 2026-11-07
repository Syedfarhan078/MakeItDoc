import unittest
from PIL import Image
import io
from processors.image_tools import (
    open_image,
    rotate_image,
    flip_image,
    crop_image,
    resize_image,
    adjust_image,
    add_text_to_image,
    export_image,
    ImageProcessingError,
)


class TestImageTools(unittest.TestCase):
    def setUp(self):
        # Create a simple test RGBA image
        self.img = Image.new("RGBA", (200, 100), color=(255, 0, 0, 255))
        # Add a colored rectangle to test transforms
        for x in range(50):
            for y in range(50):
                self.img.putpixel((x, y), (0, 255, 0, 255))

    def test_open_image_bytes(self):
        buf = io.BytesIO()
        self.img.save(buf, format="PNG")
        opened = open_image(buf.getvalue())
        self.assertEqual(opened.size, (200, 100))

    def test_rotate_image(self):
        # 90 degrees clockwise -> width and height should swap
        rotated_90 = rotate_image(self.img, 90)
        self.assertEqual(rotated_90.size, (100, 200))

        # 180 degrees -> same dimensions
        rotated_180 = rotate_image(self.img, 180)
        self.assertEqual(rotated_180.size, (200, 100))

        # 270 degrees -> width and height should swap
        rotated_270 = rotate_image(self.img, 270)
        self.assertEqual(rotated_270.size, (100, 200))

    def test_flip_image(self):
        flipped_h = flip_image(self.img, horizontal=True, vertical=False)
        self.assertEqual(flipped_h.size, (200, 100))
        # Originally pixel (0,0) was green (0, 255, 0, 255)
        # After horizontal flip, pixel (199, 0) should be green
        self.assertEqual(flipped_h.getpixel((199, 0)), (0, 255, 0, 255))

    def test_crop_image(self):
        cropped = crop_image(self.img, 10, 10, 90, 60)
        self.assertEqual(cropped.size, (80, 50))

        # Test invalid crop raises ImageProcessingError
        with self.assertRaises(ImageProcessingError):
            crop_image(self.img, 50, 50, 50, 50)

    def test_resize_image(self):
        # Maintain aspect ratio
        resized_fit = resize_image(self.img, 100, 100, maintain_aspect_ratio=True)
        # Original was 200x100 (2:1). Fitted in 100x100 becomes 100x50
        self.assertEqual(resized_fit.size, (100, 50))

        # Without maintaining aspect ratio
        resized_exact = resize_image(self.img, 80, 80, maintain_aspect_ratio=False)
        self.assertEqual(resized_exact.size, (80, 80))

    def test_adjust_image(self):
        adjusted = adjust_image(self.img, brightness=1.5, contrast=1.2, saturation=0.8)
        self.assertEqual(adjusted.size, (200, 100))

    def test_add_text_to_image(self):
        with_text = add_text_to_image(self.img, "Test Text", font_size=20)
        self.assertEqual(with_text.size, (200, 100))

    def test_export_image(self):
        png_bytes = export_image(self.img, output_format="PNG")
        self.assertTrue(len(png_bytes) > 0)
        opened = Image.open(io.BytesIO(png_bytes))
        self.assertEqual(opened.format, "PNG")

        jpeg_bytes = export_image(self.img, output_format="JPEG", quality=85)
        self.assertTrue(len(jpeg_bytes) > 0)
        opened_jpg = Image.open(io.BytesIO(jpeg_bytes))
        self.assertEqual(opened_jpg.format, "JPEG")


if __name__ == "__main__":
    unittest.main()
