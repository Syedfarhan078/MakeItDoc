from django.test import TestCase, Client
from django.urls import reverse


class ImageEditorViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_dashboard_contains_image_editor_link(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("image_editor"))
        self.assertContains(response, "Image Editor")

    def test_image_editor_view_returns_200(self):
        response = self.client.get(reverse("image_editor"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tools/image_editor.html")
        self.assertContains(response, "Image Editor")
        self.assertContains(response, "mainCanvas")
        self.assertContains(response, "cropOverlay")
        self.assertContains(response, "undoBtn")
        self.assertContains(response, "redoBtn")
        self.assertContains(response, "sliderBrightness")
        self.assertContains(response, "rotateLeftBtn")
        self.assertContains(response, "resizeWidth")
        self.assertContains(response, "addTextBtn")
        self.assertContains(response, "exportDownloadBtn")
