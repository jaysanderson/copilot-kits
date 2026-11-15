"""Page-level splitting of an uploaded PDF/image into individually-ingestable pages.

This is the app's own orchestration layer (per the brief), not an ARAG call -
knowing the true page boundaries from the source file is more reliable than
asking a model to guess them. Each page becomes its own KB resource so ARAG's
classification is scoped per page (arag_client.classify_page); consecutive
same-typed pages are then merged back into one logical "document" with a page
range by pipeline.py.
"""
import io
import os
import tempfile
from pypdf import PdfReader, PdfWriter
from pdf2image import convert_from_path

IMAGE_MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


class Page:
    def __init__(self, page_number: int, upload_bytes: bytes, upload_mime: str,
                 upload_filename: str, image_path: str):
        self.page_number = page_number
        self.upload_bytes = upload_bytes
        self.upload_mime = upload_mime
        self.upload_filename = upload_filename
        self.image_path = image_path  # local PNG for legibility check + UI thumbnail


def split_file(filename: str, content: bytes, work_dir: str) -> list[Page]:
    """Returns one Page per page in the source file, numbered from 1."""
    ext = os.path.splitext(filename)[1].lower()
    os.makedirs(work_dir, exist_ok=True)

    if ext in IMAGE_MIME:
        image_path = os.path.join(work_dir, f"p1.png")
        from PIL import Image
        Image.open(io.BytesIO(content)).convert("RGB").save(image_path, "PNG")
        return [Page(1, content, IMAGE_MIME[ext], filename, image_path)]

    if ext != ".pdf":
        raise ValueError(f"unsupported file type: {ext}")

    src_path = os.path.join(work_dir, "source.pdf")
    with open(src_path, "wb") as f:
        f.write(content)

    reader = PdfReader(src_path)
    n_pages = len(reader.pages)
    rendered = convert_from_path(src_path, dpi=150)

    pages = []
    for i in range(n_pages):
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        buf = io.BytesIO()
        writer.write(buf)
        page_bytes = buf.getvalue()

        image_path = os.path.join(work_dir, f"p{i + 1}.png")
        if i < len(rendered):
            rendered[i].save(image_path, "PNG")

        base = os.path.splitext(filename)[0]
        pages.append(Page(i + 1, page_bytes, "application/pdf", f"{base}-p{i + 1}.pdf", image_path))
    return pages
