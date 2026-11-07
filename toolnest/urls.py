from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tools/image-to-pdf/", views.image_to_pdf, name="image_to_pdf"),
    path("tools/word-to-pdf/", views.word_to_pdf, name="word_to_pdf"),
    path("tools/pdf-to-word/", views.pdf_to_word, name="pdf_to_word"),
    path("tools/merge-pdf/", views.merge_pdf, name="merge_pdf"),
    path("tools/split-pdf/", views.split_pdf, name="split_pdf"),
    path("tools/rotate-pdf/", views.rotate_pdf, name="rotate_pdf"),
    path("tools/compress-pdf/", views.compress_pdf, name="compress_pdf"),
    path("tools/<slug:tool_slug>/", views.tool_page, name="tool_page"),

]