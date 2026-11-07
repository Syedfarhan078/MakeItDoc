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


class CollageMakerViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_dashboard_contains_collage_maker_link(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("collage_maker"))
        self.assertContains(response, "Collage Maker")

    def test_collage_maker_view_returns_200(self):
        response = self.client.get(reverse("collage_maker"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tools/collage_maker.html")
        self.assertContains(response, "Collage Maker")
        self.assertContains(response, "collageCanvas")
        self.assertContains(response, "addPhotosBtn")
        self.assertContains(response, "shuffleBtn")
        self.assertContains(response, "canvasRatioSelect")
        self.assertContains(response, "spacingRange")
        self.assertContains(response, "radiusRange")
        self.assertContains(response, "layoutCardsGrid")
        self.assertContains(response, "exportDownloadBtn")


class QuickNotesViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_dashboard_contains_quick_notes_link(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("quick_notes"))
        self.assertContains(response, "Quick Notes")

    def test_quick_notes_view_returns_200(self):
        response = self.client.get(reverse("quick_notes"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tools/quick_notes.html")
        self.assertContains(response, "Quick Notes")
        self.assertContains(response, "notesCanvas")
        self.assertContains(response, "excalidraw-island-top")
        self.assertContains(response, "propsPanel")
        self.assertContains(response, "boardTitleInput")
        self.assertContains(response, "undoBtn")
        self.assertContains(response, "redoBtn")
        self.assertContains(response, "exportPngBtn")
        self.assertContains(response, "exportSvgBtn")
        self.assertContains(response, "exportJsonBtn")
        self.assertContains(response, "fontSizeSegments")
        self.assertContains(response, "fontSizeRange")
        self.assertContains(response, "fontSizeDisplay")
        self.assertContains(response, "decFontSizeBtn")
        self.assertContains(response, "incFontSizeBtn")
        self.assertContains(response, "fontFamilySegments")
        self.assertContains(response, "sizePropGroup")
        self.assertContains(response, "propWidthInput")
        self.assertContains(response, "propHeightInput")


