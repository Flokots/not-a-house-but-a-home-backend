import os
import io
import fitz  # PyMuPDF
import qrcode
import requests
from io import BytesIO
from PIL import Image
from django.conf import settings
from nahbah.models import Design
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import landscape

BASE_URL = settings.BASE_URL  # Use settings instead of hardcoded
INTRO_PDF_PATH = os.path.join(settings.STATIC_ROOT, "not_a_house_but_a_home_intro_pages.pdf")
CREDITS_IMAGE_PATH = os.path.join(settings.STATIC_ROOT, "doodle.png")
A6 = landscape((148 * mm, 105 * mm))


def generate_qr_code(url):
    qr = qrcode.QRCode(box_size=2, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    stream = io.BytesIO()
    img.save(stream, format="PNG")
    stream.seek(0)
    return stream


def add_intro_pages(pdf_writer):
    if os.path.exists(INTRO_PDF_PATH):
        intro_doc = fitz.open(INTRO_PDF_PATH)
        for page in intro_doc:
            pdf_writer.insert_pdf(intro_doc, from_page=page.number, to_page=page.number)
        intro_doc.close()


def add_design_entry(design, pdf_writer):
    # Page 1: Metadata with wrapped text
    meta_page = fitz.open()
    page = meta_page.new_page(width=A6[0], height=A6[1])
    
    # Title
    title_rect = fitz.Rect(30, 30, A6[0] - 30, 60)
    page.insert_textbox(title_rect, design.title, fontsize=14, fontname="hebo")
    
    # Material
    material_rect = fitz.Rect(30, 65, A6[0] - 30, 85)
    page.insert_textbox(material_rect, f"Material: {design.material.name}", fontsize=10, fontname="helv")
    
    # Description (with text wrapping, but no overflow continuation)
    desc_rect = fitz.Rect(30, 90, A6[0] - 100, A6[1] - 50)
    page.insert_textbox(desc_rect, design.description, fontsize=9, fontname="helv", align=fitz.TEXT_ALIGN_LEFT)
    
    # Contributor
    contributor = design.contributor.name if design.contributor else "Anonymous"
    contrib_rect = fitz.Rect(30, A6[1] - 45, A6[0] - 100, A6[1] - 30)
    page.insert_textbox(contrib_rect, f"Contributor: {contributor}", fontsize=9, fontname="helv")
    
    # QR Code
    qr_stream = generate_qr_code(f"{BASE_URL}/designs/{design.id}")
    qr_img = fitz.Pixmap(qr_stream.read())
    page.insert_image(fitz.Rect(A6[0] - 90, 20, A6[0] - 20, 90), pixmap=qr_img, keep_proportion=True)
    
    pdf_writer.insert_pdf(meta_page)
    meta_page.close()

    # Pages 2+: Full Design File (PDF or Image from Cloudinary)
    if design.design_file:
        try:
            file_url = design.design_file.url
            response = requests.get(file_url)
            response.raise_for_status()
            file_stream = BytesIO(response.content)
            
            # Check if it's a PDF by trying to open it
            try:
                design_doc = fitz.open(stream=file_stream, filetype="pdf")
                pdf_writer.insert_pdf(design_doc)
                design_doc.close()
            except:
                # Not a PDF, treat as image
                file_stream.seek(0)
                img_doc = fitz.open()
                img_page = img_doc.new_page(width=A6[0], height=A6[1])
                img = fitz.Pixmap(file_stream)
                rect = fitz.Rect(10, 10, A6[0] - 10, A6[1] - 10)
                img_page.insert_image(rect, pixmap=img, keep_proportion=True)
                pdf_writer.insert_pdf(img_doc)
                img_doc.close()
        except Exception as e:
            # Add error page if file loading fails
            error_page = fitz.open()
            err_pg = error_page.new_page(width=A6[0], height=A6[1])
            err_pg.insert_textbox(fitz.Rect(30, 50, A6[0] - 30, A6[1] - 50), 
                                 f"Error loading design file: {str(e)}", 
                                 fontsize=10, fontname="helv")
            pdf_writer.insert_pdf(error_page)
            error_page.close()


def add_credits_page(pdf_writer):
    credits = fitz.open()
    page = credits.new_page(width=A6[0], height=A6[1])
    text = (
        "Text by:\nDányi Tibor Zoltán (architect)\n\n"
        "Drawings by:\nDányi Tibor Zoltán (architect)\nTamás Pethes (architect)\n\n"
        "Edited by:\nDányi Tibor Zoltán (architect)\nNicolás Ramos González (architect)"
    )

    page.insert_text((30, 40), text, fontsize=10)
    
    # Add doodle image
    if os.path.exists(CREDITS_IMAGE_PATH):
        doodle = fitz.Pixmap(CREDITS_IMAGE_PATH)
        rect = fitz.Rect(160.76, 0.75, 260.76, 78.35)
        page.insert_image(rect, pixmap=doodle, keep_proportion=True)

    # QR Code to Home
    qr_stream = generate_qr_code(BASE_URL)
    qr_img = fitz.Pixmap(qr_stream.read())
    page.insert_image(fitz.Rect(350, 20, 420, 90), pixmap=qr_img, keep_proportion=True)
    pdf_writer.insert_pdf(credits)
    credits.close()


def generate_booklet(design_ids):
    pdf_writer = fitz.open()
    add_intro_pages(pdf_writer)

    for design in Design.objects.filter(id__in=design_ids, status="approved"):
        add_design_entry(design, pdf_writer)

    add_credits_page(pdf_writer)

    output_stream = io.BytesIO()
    pdf_writer.save(output_stream)
    pdf_writer.close()
    output_stream.seek(0)
    return output_stream
