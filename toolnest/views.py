import os
import shutil
import subprocess
import tempfile
import zipfile
import pymupdf
from pdf2docx import Converter

from pathlib import Path

from django.shortcuts import render
from django.http import Http404

from io import BytesIO
from django.http import FileResponse
from django.views.decorators.http import require_http_methods
from PIL.Image import DecompressionBombError, DecompressionBombWarning
from PIL import (
    Image, 
    ImageOps, 
    UnidentifiedImageError,
)
import warnings


Image.MAX_IMAGE_PIXELS = 25_000_000
warnings.simplefilter("error", DecompressionBombWarning)

# Create your views here.
TOOLS = {
    "merge-pdf": {
        "title": "Merge PDf",
        "description": "Combine multiple PDF files into one document.",
        "category": "PDF Tools",
    },

    "split-pdf": {
        "title": "Split PDF",
        "description": "Extract the pages you need from a PDF",
        "category": "PDF Tools",
    },

    "rotate-pdf": {
        "title": "Rotate PDF",
        "description": "Change the orientation of PDF pages",
        "category": "PDF Tools",
    },
    
     "image-to-pdf": {
        "title": "Image to PDF",
        "description": "Combine images into a single PDF document.",
        "category": "PDF Tools",
    },
    "word-to-pdf": {
        "title": "Word to PDF",
        "description": "Convert Word documents into PDF files.",
        "category": "PDF Tools",
    },
    "pdf-to-word": {
        "title": "PDF to Word",
        "description": "Convert PDF documents into editable Word files.",
        "category": "PDF Tools",
    },
    "notes": {
        "title": "Quick Notes",
        "description": "Capture thoughts and keep useful notes in one place.",
        "category": "Workspace",
    },
    "image-editor": {
        "title": "Image Editor",
        "description": "Add text, crop images and make quick edits.",
        "category": "Creative Tools",
    },
    "collage-maker": {
        "title": "Collage Maker",
        "description": "Arrange multiple photos into a single collage.",
        "category": "Creative Tools",
    },
}


def dashboard(request):
    return render(request, "dashboard.html", {"tools": TOOLS})

def tool_page(request, tool_slug):
    tool = TOOLS.get(tool_slug)

    if tool is None:
        raise Http404("Tool not found")
    
    return render(
        request,
        "tools/placeholder.html",
        {"tool": tool, "tool_slug": tool_slug},
    )


# Image to PDF
MAX_IMAGE_COUNT = 20
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 mb per image
MAX_TOTAL_SIZE = 40 * 1024 * 1024  # 40 MB PER IMAGE
MAX_IMAGE_PIXELS = 25_000_000
MAX_TOTAL_PIXELS = 100_000_000

ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}

# WORD TO PDF SETTINGS
MAX_WORD_FILE_SIZE = 20 * 1024 * 1024 
MAX_DOCX_UNCOMPRESSED_SIZE = 100 * 1024 * 1024 # 100 MB
MAX_DOCX_FILES = 5000
WORD_CONVERSION_TIMEOUT = 60

# PDF TO WORD SETTINGS (same used for pdf rotation)
MAX_PDF_FILE_SIZE = 20 * 1024 * 1024
MAX_PDF_PAGES = 100

#MERGE PDF SETTINGS
MAX_MERGE_FILES = 10
MAX_MERGE_TOTAL_SIZE = 100 * 1024 * 1024       #100 MB
MAX_MERGE_TOTAL_PAGES = 300

#SPLIT PDF SETTINGS
MAX_SPLIT_OUTPUT_FILES = 100

PDF_DPI = 150

A4_WIDTH = 1240
A4_HEIGHT = 1754

MARGIN_OPTIONS = {
    "none": 0,
    "small": 30,
    "large": 75,
}

def prepare_pdf_page(image, page_width, page_height, margin, fit_mode):
    available_width = page_width - (2 * margin)
    available_height = page_height - (2 * margin)

    if available_width <= 0 or available_height <= 0:
        raise ValueError("The selected margins are too large")

    if fit_mode == "fit":
        page_image = Image.new("RGB", (page_width, page_height), "white")
        fitted = ImageOps.contain(
            image,
            (available_width, available_height),
            method=Image.Resampling.LANCZOS,
        )

        x = (page_width - fitted.width) // 2
        y = (page_height - fitted.height) // 2

        page_image.paste(fitted, (x, y))
        fitted.close()
    
    elif fit_mode == "fill":
        page_image = Image.new("RGB", (page_width, page_height), "white")
        filled = ImageOps.fit(
            image,
            (available_width, available_height),
            method=Image.Resampling.LANCZOS,
            centering = (0.5, 0.5),
        )

        page_image.paste(filled, (margin, margin))
        filled.close()
    
    else:
        page_image = Image.new("RGB", (page_width, page_height), "white")

        x = (page_width - image.width) // 2
        y = (page_height - image.height) // 2

        page_image.paste(image, (x, y))
    
    return page_image
  
@require_http_methods(["GET", "POST"])
def image_to_pdf(request):
    if request.method == "GET":
        return render(request, "tools/image_to_pdf.html")
    
    uploaded_images = request.FILES.getlist("images")

    if not uploaded_images:
        return render(
            request,
            "tools/image_to_pdf.html",
            {"error": "Please select at least one image."},
        )

    if len(uploaded_images) > MAX_IMAGE_COUNT:
        return render(
            request,
            "tools/image_to_pdf.html",
            {"error": f"You can uplload at most {MAX_IMAGE_COUNT} images."}
        )
    
    total_size = sum(image.size for image in uploaded_images)

    if total_size > MAX_TOTAL_SIZE:
        return render(
            request,
            "tools/image_to_pdf.html",
            {"error": "The combined image size must not exceed 40 MB"},
        )

    for uploaded in uploaded_images:
        if uploaded.size == 0:
            return render(
                request,
                "tools/image_to_pdf.html",
                {"error": "One of the selected file is empty."},
            )

        if uploaded.size > MAX_IMAGE_SIZE:
            return render(
                request,
                "tools/image_to_pdf.html",
                {"error": "Each image must be 10 MB or smaller"},
            )
    
    page_size = request.POST.get("page_size", "a4")
    orientation = request.POST.get("orientation", "portrait")
    fit_mode = request.POST.get("fit_mode", "fit")
    margin_choice = request.POST.get("margin", "small")

    if page_size not in {"a4", "original"}:
        page_size = "a4"
    
    if orientation not in {"portrait", "landscape"}:
        orientation = "portrait"

    if fit_mode not in {"fit", "fill", "original"}:
        fit_mode = "fit"
    
    if margin_choice not in MARGIN_OPTIONS:
        margin_choice = "small"

    margin = MARGIN_OPTIONS[margin_choice]

    
    pdf_images = []
    total_pixels = 0

    try:
        for uploaded in uploaded_images:
            with Image.open(uploaded) as image:

                image_pixels = image.width * image.height

                if image_pixels > MAX_IMAGE_PIXELS:
                    raise ValueError(
                        f"{uploaded.name} exceeds the 25-megapixels limit."
                    )
                
                total_pixels += image_pixels

                if total_pixels > MAX_TOTAL_PIXELS:
                    raise ValueError(
                        "The combined images exceed the 100-megapixels limit."
                    )
                


                if image.format not in ALLOWED_IMAGE_FORMATS:
                    raise ValueError(
                        "Only JPG, JPEG, and PNG images are supported."
                    )
                image.verify()

            uploaded.seek(0)

            with Image.open(uploaded) as image:
                image = ImageOps.exif_transpose(image)
                image.load()

                if image.mode == "RGBA":
                    background = Image.new(
                        "RGB", image.size, "white"
                    )
                    background.paste(image, mask=image.getchannel("A"))
                    image = background
                else:
                    image = image.convert("RGB")

                pdf_images.append(image.copy())

    except (UnidentifiedImageError, 
            OSError, 
            Image.DecompressionBombError, 
            DecompressionBombWarning,
        ):
        for image in pdf_images:
            image.close()

        return render(
            request,
            "tools/image_to_pdf.html",
            {"error": "An image is invalid, damaged, or too large to process."},
        )

    
    except ValueError as exc:
        for image in pdf_images:
            image.close()

        return render(
            request,
            "tools/image_to_pdf.html",
            {"error": str(exc)},
        )

    pdf_pages = []

    try:
        for image in pdf_images:
            if page_size == "a4":
                page_width, page_height = A4_WIDTH, A4_HEIGHT

                if orientation == "landscape":
                    page_width, page_height = page_height, page_width

            else:
                page_width = image.width + (2 * margin)
                page_height = image.height + (2 * margin)
            
            page = prepare_pdf_page(
                image,
                page_width,
                page_height,
                margin,
                fit_mode,
            )

            pdf_pages.append(page)


        pdf_buffer = BytesIO()

        pdf_pages[0].save(
            pdf_buffer,
            format="PDF",
            save_all = True,
            append_images = pdf_pages[1:],
            resolution = PDF_DPI,
        )

        pdf_buffer.seek(0)

        first_stem = Path(uploaded_images[0].name).stem.replace('"', '').strip() if uploaded_images and uploaded_images[0].name else "images"
        out_filename = f"{first_stem}-MakeitDoc.pdf"

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=out_filename,
            content_type="application/pdf",
        )
    
    except (OSError, ValueError, Image.DecompressionBombError):
        return render(
            request,
            "tools/image_to_pdf.html",
            {
                "error": (
                    "Something went wrong while generating the PDF."
                    "Please try again with different images or settings."
                )
            },
        )

    
    finally:
        for image in pdf_images:
            image.close()

        for page in pdf_pages:
            page.close()

        

def validate_docx(file_path):
    try:
        with zipfile.ZipFile(file_path, "r") as docx:
            file_list = docx.infolist()

            if len(file_list) > MAX_DOCX_FILES:
                raise ValueError("The document contains too many files.")

            total_uncompressed_size = sum(
                item.file_size for item in file_list
            )

            if total_uncompressed_size > MAX_DOCX_UNCOMPRESSED_SIZE:
                raise ValueError(
                    "The document is too large to process safely."
                )

            required_files = {
                "[Content_Types].xml",
                "word/document.xml",
            }

            available_files = set(docx.namelist())

            if not required_files.issubset(available_files):
                raise ValueError("The uploaded file is not a Valid Word Document.")

            bad_file = docx.testzip()

            if bad_file is not None:
                raise ValueError("The Word document appears to be damaged.")

    except zipfile.BadZipFile:
        raise ValueError("The uploaded file is not a valid DOCX document.")

def validate_pdf(file_path):
    try:
        with pymupdf.open(file_path) as pdf:

            if pdf.is_encrypted:
                raise ValueError(
                    "Password-protected PDFs are not supported."
                )

            if len(pdf) == 0:
                raise ValueError(
                    "The PDF does not contain any pages."
                )
            
            if len(pdf) > MAX_PDF_PAGES:
                raise ValueError(
                    f"PDF files can contain a maximum of {MAX_PDF_PAGES} pages."
                )

            extracted_text = ""

            for page in pdf:
                extracted_text += page.get_text().strip()

            if not extracted_text:
                raise ValueError(
                    "No selectable text was found. "
                    "Scanned PDFs are not supported yet."
                )
    except pymupdf.FileDataError:
        raise ValueError("The uplaoded PDF is damaged or invalid.")
    
    except RuntimeError:
        raise ValueError("The PDF could not be opened or processed.")

@require_http_methods(["GET", "POST"])
def word_to_pdf(request):

    if request.method == "GET":
        return render(request, "tools/word_to_pdf.html")
    
    uploaded_files = request.FILES.get("document")

    if not uploaded_files:
        return render(
            request,
            "tools/word_to_pdf.html",
            {"error": "Please select a Word document."},
        )

    if uploaded_files.size == 0:
        return render(
            request,
            "tools/word_to_pdf.html",
            {"error": "The selected file is empty."},
        )

    if uploaded_files.size > MAX_WORD_FILE_SIZE:
        return render(
            request,
            "tools/word_to_pdf.html",
            {"error": "The maximum file size allowed is 20 MB."},
        )

    if not uploaded_files.name.lower().endswith(".docx"):
        return render(
            request,
            "tools/word_to_pdf.html",
            {"error": "Only .docx Word documents are supported."},
        )

    soffice_path = shutil.which("soffice") or shutil.which("libreoffice")
    abiword_path = shutil.which("abiword")

    if not soffice_path and not abiword_path:
        return render(
            request,
            "tools/word_to_pdf.html",
            {
                "error": (
                    "No document conversion engine (LibreOffice or AbiWord) was found on this server. "
                    "Please install LibreOffice or AbiWord to enable Word to PDF conversion."
                )
            },
        )

    try:
        with tempfile.TemporaryDirectory(prefix="toolnest_word_") as temp_dir:
            temp_path = Path(temp_dir)

            input_dir = temp_path / "input"
            output_dir = temp_path / "output"
            profile_dir = temp_path / "profile"

            input_dir.mkdir()
            output_dir.mkdir()
            profile_dir.mkdir()

            input_file = input_dir / "document.docx"
            output_file = output_dir / "document.pdf"

            with input_file.open("wb") as destination:
                for chunk in uploaded_files.chunks():
                    destination.write(chunk)

            validate_docx(input_file)

            result = None

            # Try LibreOffice if available
            if soffice_path:
                command = [
                    soffice_path,
                    "--headless",
                    "--nologo",
                    "--nodefault",
                    "--nofirststartwizard",
                    f"-env:UserInstallation={profile_dir.as_uri()}",
                    "--convert-to",
                    "pdf:writer_pdf_Export",
                    "--outdir",
                    str(output_dir),
                    str(input_file),
                ]
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=WORD_CONVERSION_TIMEOUT,
                    check=False,
                )

            # Fallback to AbiWord if soffice is not installed or failed to produce output
            if (not soffice_path or result.returncode != 0 or not output_file.exists()) and abiword_path:
                abi_command = [
                    abiword_path,
                    "--to=pdf",
                    str(input_file),
                    "-o",
                    str(output_file),
                ]
                result = subprocess.run(
                    abi_command,
                    capture_output=True,
                    text=True,
                    timeout=WORD_CONVERSION_TIMEOUT,
                    check=False,
                )
                if not output_file.exists():
                    fallback_in_input = input_dir / "document.pdf"
                    if fallback_in_input.exists():
                        shutil.move(str(fallback_in_input), str(output_file))

            if not output_file.exists() or (result and result.returncode != 0 and not output_file.exists()):
                raise RuntimeError("Document conversion failed.")
            
            if output_file.stat().st_size == 0:
                raise RuntimeError("The generated PDF is empty.")

            pdf_data = output_file.read_bytes()

            if not pdf_data.startswith(b"%PDF-"):
                raise RuntimeError("The generated file is not a valid PDF.")
            
        pdf_buffer = BytesIO(pdf_data)

        base_stem = Path(uploaded_files.name).stem.replace('"', '').strip() if uploaded_files and uploaded_files.name else "document"
        out_filename = f"{base_stem}-MakeitDoc.pdf"

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=out_filename,
            content_type="application/pdf",
        )
    
    except ValueError as exc:
        return render(
            request,
            "tools/word_to_pdf.html",
            {
                "error": (
                    "Conversion took too long. "
                    "Please try a smaller or simpler document."
                )
            },
        )
    
    except (OSError, RuntimeError, zipfile.LargeZipFile):
        return render(
            request,
            "tools/word_to_pdf.html",
            {
                "error": (
                    "Something went wrong while converting your document. "
                    "Please try again with another DOCX File."
                )
            },
        )


@require_http_methods(["GET", "POST"])
def pdf_to_word(request):

    if request.method == "GET":
        return render(request, "tools/pdf_to_word.html")
    
    uploaded_file = request.FILES.get("document")

    if not uploaded_file:
        return render(
            request,
            "tools/pdf_to_word.html",
            {"error": "Please select a PDF document."},
        )

    if uploaded_file.size == 0:
        return render(
            request,
            "tools/pdf_to_word.html",
            {"error": "The selected file is empty."},
        )

    if uploaded_file.size > MAX_PDF_FILE_SIZE:
        return render(
            request,
            "tools/pdf_to_word.html",
            {"error": "The maximum file size allowed is 20 MB."},
        )
    
    if not uploaded_file.name.lower().endswith(".pdf"):
        return render(
            request,
            "tools/pdf_to_word.html",
            {"error": "Only PDF files are supported."},
        )

    try:
        with tempfile.TemporaryDirectory(prefix="toolnest_pdf_") as temp_dir:
            temp_path = Path(temp_dir)

            input_file = temp_path / "document.pdf"
            output_file = temp_path / "document.pdf"

            with input_file.open("wb") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            validate_pdf(input_file)

            converter = Converter(str(output_file))

            try:
                converter.convert(str(output_file))
            finally:
                converter.close()

            
            if not output_file.exists():
                raise RuntimeError("Word document was not generated.")

            if output_file.stat().st_size == 0:
                raise RuntimeError("The generated word document is empty.")

            docx_data = output_file.read_bytes()

        base_stem = Path(uploaded_file.name).stem.replace('"', '').strip() if uploaded_file and uploaded_file.name else "document"
        out_filename = f"{base_stem}-MakeitDoc.docx"

        return FileResponse(
            BytesIO(docx_data),
            as_attachment=True,
            filename=out_filename,
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )
    
    except ValueError as exc:
        return render(
            request,
            "tools/pdf_to_word.html",
            {"error": str(exc)},
        )

    except (OSError, RuntimeError, pymupdf.FileDataError):
        return render(
            request,
            "tools/pdf_to_word.html",
            {
                "error": (
                    "Something went wrong while converting your PDF. "
                    "Please try another document."
                )
            },
        )

    except Exception:
        return render(
            request,
            "tools/pdf_to_word.html",
            {
                "error": (
                    "The PDF could not be converted. "
                    "Please try another document."
                )
            },
        )


@require_http_methods(["GET", "POST"])
def merge_pdf(request):

    if request.method == "GET":
        return render(request, "tools/merge_pdf.html")
    
    uploaded_files = request.FILES.getlist("documents")

    if len(uploaded_files) < 2:
        return render(
            request,
            "tools/merge_pdf.html",
            {"error": "Please select at least two PDF Files."},
        )

    if len(uploaded_files) > MAX_MERGE_FILES:
        return render(
            request,
            "tools/merge_pdf.html",
            {"error": f"You can merge a maximum of {MAX_MERGE_FILES} PDF files."},
        )

    total_size = sum(file.size for file in uploaded_files)

    if total_size > MAX_MERGE_TOTAL_SIZE:
        return render(
            request,
            "tools/merge_pdf.html",
            {"error": "The combined file size must not exceed 100 MB."},
        )

    for uploaded_file in uploaded_files:
        if uploaded_file.size == 0:
            return render(
                request,
                "tools/merge_pdf.html",
                {"error": "One of the selected files is empty."},
            )

        if uploaded_file.size > MAX_PDF_FILE_SIZE:
            return render(
                request,
                "tools/merge_pdf.html",
                {"error": "Each PDF file must be 20 MB or smaller."},
            )
        
        if not uploaded_file.name.lower().endswith(".pdf"):
            return render(
                request,
                "tools/merge_pdf.html",
                {"error": "Only PDF files are supported."},
            )
        
        merged_pdf = pymupdf.open()
        total_pages = 0

        try:
            with tempfile.TemporaryDirectory(prefix="toolnest_merge_") as temp_dir:
                temp_path = Path(temp_dir)

                for index, uploaded_file in enumerate(uploaded_files):
                    input_path = temp_path / f"document_{index}.pdf"

                    with input_path.open("wb") as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)
                    
                    with pymupdf.open(input_path) as source_pdf:
                        if source_pdf.is_encrypted:
                            raise ValueError(
                                f"{uploaded_file.name} is password protected."
                            )
                        
                        if len(source_pdf) == 0:
                            raise ValueError(
                                f"{uploaded_file.name} contains no pages."
                            )
                        total_pages += len(source_pdf)


                        if total_pages > MAX_MERGE_TOTAL_PAGES:
                            raise ValueError(
                                "The combined PDFs cannot exceed 300 pages."
                            )
                        
                        merged_pdf.insert_pdf(source_pdf)
                
                if merged_pdf.page_count == 0:
                    raise ValueError("No pages were available to merge.")
                
                pdf_buffer = BytesIO(merged_pdf.tobytes())

            base_stem = Path(uploaded_files[0].name).stem.replace('"', '').strip() if uploaded_files and uploaded_files[0].name else "merged"
            out_filename = f"{base_stem}-merged-MakeitDoc.pdf"

            return FileResponse(
                pdf_buffer,
                as_attachment=True,
                filename=out_filename,
                content_type = "application/pdf",
            )
        
        except ValueError as exc:
            return render(
                request,
                "tools/merge_pdf.html",
                {"error": str(exc)},
            )

        except (OSError, RuntimeError, pymupdf.FileDataError):
            return render(
                request,
            "tools/merge_pdf.html",
            {
                "error": (
                    "Something went wrong while merging your PDFs. "
                    "Please check your files and try again."
                )
            },
        )

        finally:
            merged_pdf.close()


@require_http_methods(["GET", "POST"])
def split_pdf(request):
    if request.method == "GET":
        return render(request, "tools/split_pdf.html")
    
    uploaded_file = request.FILES.get("document")
    split_mode = request.POST.get("split_mode")
    page_range = request.POST.get("page_range", "").strip()

    if not uploaded_file:
        return render(
            request,
            "tools/split_to_pdf.html",
            {"error": "Please select a PDF file."},
        )

    if uploaded_file.size == 0:
        return render(
            request,
            "tools/split_pdf.html",
            {"error": "The selected file is empty."},
        )
    
    if uploaded_file.size > MAX_PDF_FILE_SIZE:
         return render(
            request,
            "tools/split_pdf.html",
            {"error": "The PDF file must be 20 MB or smaller."},
        )

    if not uploaded_file.name.lower().endswith(".pdf"):
        return render(
            request,
            "tools/split_pdf.html",
            {"error": "Only PDF files are supported."},
        )
    
    try:
        with pymupdf.open(stream = uploaded_file.read(), filetype="pdf") as source_pdf:

            if source_pdf.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported.")
            
            total_pages = len(source_pdf)

            if tool_page == 0:
                raise ValueError("The PDF contains no pages.")
            
            if total_pages > MAX_PDF_PAGES:
                raise ValueError(
                    f"The PDF cannot contain more than {MAX_PDF_PAGES} pages."
                )
            
            if split_mode == "individual":

                if total_pages > MAX_SPLIT_OUTPUT_FILES:
                    raise ValueError("Too many output files.")
                
                zip_buffer = BytesIO()

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for page_number in range(total_pages):
                        output_pdf = pymupdf.open()

                        try:
                            output_pdf.insert_pdf(
                                source_pdf,
                                from_page = page_number,
                                to_page=page_number,
                            )
                        
                            pdf_bytes = output_pdf.tobytes()

                            zip_file.writestr(
                                f"page_{page_number + 1}.pdf",
                                pdf_bytes,
                            )
                        finally:
                            output_pdf.close()

                zip_buffer.seek(0)

                base_stem = Path(uploaded_file.name).stem.replace('"', '').strip() if uploaded_file and uploaded_file.name else "split"

                return FileResponse(
                    zip_buffer,
                    as_attachment=True,
                    filename=f"{base_stem}-split-MakeitDoc.zip",
                    content_type = "application/zip",
                )
                    
            elif split_mode == "custom":
                try:
                    start_page, end_page = map(
                        int, page_range.split("-")
                    )

                except (ValueError, TypeError):
                    raise ValueError(
                        "Enter a valid page range, such as 1-5."
                    )

                if start_page < 1 or end_page < start_page:
                    raise ValueError("Please enter a valid page range.")
                
                if end_page > total_pages:
                    raise ValueError(
                        f"This PDF contains only {total_pages} pages."
                    )

                output_pdf = pymupdf.open()

                try:
                    output_pdf.insert_pdf(
                        source_pdf,
                        from_page = start_page - 1,
                        to_page = end_page - 1,
                    )

                    pdf_buffer = BytesIO(output_pdf.tobytes())

                finally:
                    output_pdf.close()

                
                base_stem = Path(uploaded_file.name).stem.replace('"', '').strip() if uploaded_file and uploaded_file.name else "document"
                out_filename = f"{base_stem}-pages-{start_page}-{end_page}-MakeitDoc.pdf"

                return FileResponse(
                    pdf_buffer,
                    as_attachment=True,
                    filename=out_filename,
                    content_type="application/pdf",
                )

            else:
                raise ValueError("Please select a valid split option.")

    except ValueError as exc:
        return render(
            request,
            "tools/split_pdf.html",
            {"error": str(exc)},
        )

    except (OSError, RuntimeError, pymupdf.FileDataError):
        return render(
            request,
            "tools/split_pdf.html",
            {
                "error": (
                    "Something went wrong while processing your PDF. "
                    "Please check the file and try again."
                )
            },
        )

@require_http_methods(["GET", "POST"])
def rotate_pdf(request):
    if request.method == "GET":
        return render(request, "tools/rotate_pdf.html")

    uploaded_file = request.FILES.get("document")

    rotation = request.POST.get("rotation")

    if not uploaded_file:
         return render(
            request,
            "tools/rotate_pdf.html",
            {"error": "Please select a PDF file."},
        )
    
    if uploaded_file.size == 0:
        return render(
            request,
            "tools/rotate_pdf.html",
            {"error": "The selected file is empty."},
        )
    
    if uploaded_file.size > MAX_PDF_FILE_SIZE:
        return render(
            request,
            "tools/rotate_pdf.html",
            {"error": "The PDF file must be 20 MB or smaller."},
        )

    if not uploaded_file.name.lower().endswith(".pdf"):
        return render(
            request,
            "tools/rotate_pdf.html",
            {"error": "Only PDF files are supported."},
        )

    if rotation not in ["90", "180", "270"]:
        return render(
            request,
            "tools/rotate_pdf.html",
            {"error": "Please select a valid rotation angle."},
        )

    try:
        with pymupdf.open(stream=uploaded_file.read(),filetype = "pdf",) as source_pdf:
            if source_pdf.is_encrypted:
                raise ValueError(
                    "Password-protected PDFs are not supported."
                )
            
            if len(source_pdf) == 0:
                raise ValueError("The PDF contains no pages.")

            if len(source_pdf) > MAX_PDF_PAGES:
                raise ValueError(
                    f"The PDF cannot contain more than {MAX_PDF_PAGES} pages."
                )

            rotation_angle = int(rotation)

            for page in source_pdf:
                page.set_rotation(
                    (page.rotation + rotation_angle) % 360
                )

            pdf_buffer = BytesIO(
                source_pdf.tobytes(garbage=4, deflate=True)
            )

        pdf_buffer.seek(0)

        base_stem = Path(uploaded_file.name).stem.replace('"', '').strip() if uploaded_file and uploaded_file.name else "rotated"
        out_filename = f"{base_stem}-rotated-MakeitDoc.pdf"

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=out_filename,
            content_type="application/pdf",
        )

    except ValueError as exc:
        return render(
            request,
            "tools/rotate_pdf.html",
            {"error": str(exc)},
        )

    except (OSError, RuntimeError, pymupdf.FileDataError):
        return render(
            request,
            "tools/rotate_pdf.html",
            {
                "error": (
                    "Something went wrong while rotating your PDF. "
                    "Please check your file and try again."
                )
            },
        )



@require_http_methods(["GET", "POST"])
def compress_pdf(request):

    if request.method == "GET":
        return render(request, "tools/compress_pdf.html")

    uploaded_file = request.FILES.get("document")
    compression_level = request.POST.get("compression_level")

    if not uploaded_file:
        return render(
            request,
            "tools/compress_pdf.html",
            {"error": "Please select a PDF file."},
        )

    if uploaded_file.size == 0:
        return render(
            request,
            "tools/compress_pdf.html",
            {"error": "The selected file is empty."},
        )

    if uploaded_file.size > MAX_PDF_FILE_SIZE:
        return render(
            request,
            "tools/compress_pdf.html",
            {"error": "The PDF file must be 20 MB or smaller."},
        )

    if not uploaded_file.name.lower().endswith(".pdf"):
        return render(
            request,
            "tools/compress_pdf.html",
            {"error": "Only PDF files are supported."},
        )

    compression_settings = {
        "low": {
            "quality": 85,
            "dpi_threshold": 200,
            "dpi_target": 150,
        },
        "medium": {
            "quality": 75,
            "dpi_threshold": 160,
            "dpi_target": 120,
        },
        "high": {
            "quality": 60,
            "dpi_threshold": 120,
            "dpi_target": 96,
        },
    }

    if compression_level not in compression_settings:
        return render(
            request,
            "tools/compress_pdf.html",
            {"error": "Please select a valid compression level."},
        )

    try:
        settings = compression_settings[compression_level]

        with pymupdf.open(
            stream=uploaded_file.read(),
            filetype="pdf",
        ) as source_pdf:

            if source_pdf.is_encrypted:
                raise ValueError(
                    "Password-protected PDFs are not supported."
                )

            if len(source_pdf) == 0:
                raise ValueError("The PDF contains no pages.")

            if len(source_pdf) > MAX_PDF_PAGES:
                raise ValueError(
                    f"The PDF cannot contain more than {MAX_PDF_PAGES} pages."
                )

          
            source_pdf.rewrite_images(
                quality=settings["quality"],
                dpi_threshold=settings["dpi_threshold"],
                dpi_target=settings["dpi_target"],
            )

            
            pdf_buffer = BytesIO(
                source_pdf.tobytes(
                    garbage=4,
                    deflate=True,
                    deflate_images=True,
                    deflate_fonts=True,
                )
            )

        pdf_buffer.seek(0)

        base_stem = Path(uploaded_file.name).stem.replace('"', '').strip() if uploaded_file and uploaded_file.name else "compressed"
        out_filename = f"{base_stem}-compressed-MakeitDoc.pdf"

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=out_filename,
            content_type="application/pdf",
        )

    except ValueError as exc:
        return render(
            request,
            "tools/compress_pdf.html",
            {"error": str(exc)},
        )

    except (OSError, RuntimeError, pymupdf.FileDataError):
        return render(
            request,
            "tools/compress_pdf.html",
            {
                "error": (
                    "Something went wrong while compressing your PDF. "
                    "Please check your file and try again."
                )
            },
        )



@require_http_methods(["GET", "POST"])
def protect_pdf(request):

    if request.method == "GET":
        return render(request, "tools/protect_pdf.html")

    uploaded_file = request.FILES.get("document")
    password = request.POST.get("password", "")
    confirm_password = request.POST.get("confirm_password", "")

    if not uploaded_file:
        return render(
            request,
            "tools/protect_pdf.html",
            {"error": "Please select a PDF file."},
        )

    if uploaded_file.size == 0:
        return render(
            request,
            "tools/protect_pdf.html",
            {"error": "The selected file is empty."},
        )

    if uploaded_file.size > MAX_PDF_FILE_SIZE:
        return render(
            request,
            "tools/protect_pdf.html",
            {"error": "The PDF file must be 20 MB or smaller."},
        )

    if not uploaded_file.name.lower().endswith(".pdf"):
        return render(
            request,
            "tools/protect_pdf.html",
            {"error": "Only PDF files are supported."},
        )

    if len(password) < 8 or len(password) > 40:
        return render(
            request,
            "tools/protect_pdf.html",
            {"error": "Password must contain between 8 and 40 characters."},
        )

    if password != confirm_password:
        return render(
            request,
            "tools/protect_pdf.html",
            {"error": "Passwords do not match."},
        )

    try:
        with pymupdf.open(
            stream=uploaded_file.read(),
            filetype="pdf",
        ) as source_pdf:

            if source_pdf.is_encrypted:
                raise ValueError(
                    "The uploaded PDF is already password-protected."
                )

            if len(source_pdf) == 0:
                raise ValueError("The PDF contains no pages.")

            if len(source_pdf) > MAX_PDF_PAGES:
                raise ValueError(
                    f"The PDF cannot contain more than {MAX_PDF_PAGES} pages."
                )

            # Generate a separate, random owner password.
            owner_password = os.urandom(20).hex()

            pdf_buffer = BytesIO(
                source_pdf.tobytes(
                    garbage=4,
                    deflate=True,
                    encryption=pymupdf.PDF_ENCRYPT_AES_256,
                    owner_pw=owner_password,
                    user_pw=password,
                    permissions=-1,
                )
            )

        pdf_buffer.seek(0)

        base_stem = Path(uploaded_file.name).stem.replace('"', '').strip() if uploaded_file and uploaded_file.name else "protected"
        out_filename = f"{base_stem}-protected-MakeitDoc.pdf"

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=out_filename,
            content_type="application/pdf",
        )

    except ValueError as exc:
        return render(
            request,
            "tools/protect_pdf.html",
            {"error": str(exc)},
        )

    except (OSError, RuntimeError, pymupdf.FileDataError):
        return render(
            request,
            "tools/protect_pdf.html",
            {
                "error": (
                    "Something went wrong while protecting your PDF. "
                    "Please check your file and try again."
                )
            },
        )



def image_editor(request):
    return render(request, "tools/image_editor.html")


def collage_maker(request):
    return render(request, "tools/collage_maker.html")


def quick_notes(request):
    return render(request, "tools/quick_notes.html")
