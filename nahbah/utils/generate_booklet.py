import os
import io
import fitz  # PyMuPDF
import qrcode
from PIL import Image
from django.conf import settings
from nahbah.models import Design
import requests
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from django.core.files.base import ContentFile
import tempfile
from reportlab.lib.pagesizes import A6, landscape
from reportlab.lib.units import mm

# Use settings for BASE_URL
BASE_URL = settings.BASE_URL
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
    intro_doc = fitz.open(INTRO_PDF_PATH)
    for page in intro_doc:
        pdf_writer.insert_pdf(intro_doc, from_page=page.number, to_page=page.number)
    intro_doc.close()


def add_design_entry(design, pdf_writer):
    # Page 1: Metadata
    meta_page = fitz.open()
    page = meta_page.new_page(width=A6[0], height=A6[1])
    text = f"Title: {design.title} \nMaterial: {design.material.name}\n\n{design.description}"
    contributor = design.contributor.name if design.contributor else "Anonymous"
    text += f"\n\nContributor: {contributor}"

    page.insert_text((30, 50), text, fontsize=10)
    qr_stream = generate_qr_code(f"{BASE_URL}/designs/{design.id}")
    qr_img = fitz.Pixmap(qr_stream.read())
    page.insert_image(fitz.Rect(350, 20, 420, 90), pixmap=qr_img, keep_proportion=True)
    pdf_writer.insert_pdf(meta_page)
    meta_page.close()

    # Pages 2+: Full Design File (PDF or Image from Cloudinary)
    if design.design_file:
        file_url = design.design_file.url
        try:
            response = requests.get(file_url)
            response.raise_for_status()
            file_stream = BytesIO(response.content)
            
            if design.design_file.name.endswith(".pdf"):
                design_doc = fitz.open(file_stream)
                pdf_writer.insert_pdf(design_doc)
                design_doc.close()
            else:
                # Assume it's an image
                img_doc = fitz.open()
                img_page = img_doc.new_page(width=A6[0], height=A6[1])
                img = fitz.Pixmap(file_stream)
                rect = fitz.Rect(10, 10, A6[0] - 10, A6[1] - 10)
                img_page.insert_image(rect, pixmap=img, keep_proportion=True)
                pdf_writer.insert_pdf(img_doc)
                img_doc.close()
        except Exception as e:
            # Log error or add error page
            error_page = fitz.open()
            err_pg = error_page.new_page(width=A6[0], height=A6[1])
            err_pg.insert_text((30, 50), f"Error loading design file: {str(e)}", fontsize=10)
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


def generate_booklet(designs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    story = []

    for design in designs:
        # Title
        story.append(Paragraph(design.title, styles['Heading1']))
        story.append(Spacer(1, 12))

        # Description
        story.append(Paragraph(design.description, styles['Normal']))
        story.append(Spacer(1, 12))

        # Preview Image (from Cloudinary)
        if design.preview_image:
            try:
                response = requests.get(design.preview_image.url)
                response.raise_for_status()
                image_data = BytesIO(response.content)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    temp_file.write(image_data.getvalue())
                    temp_path = temp_file.name
                
                img = RLImage(temp_path, width=400, height=300)
                story.append(img)
                story.append(Spacer(1, 12))
                
                os.unlink(temp_path)
            except Exception as e:
                story.append(Paragraph(f"Error loading preview image: {str(e)}", styles['Normal']))

        # Design File (if it's an image, add it; if PDF, note it)
        if design.design_file:
            try:
                file_url = design.design_file.url
                if file_url.endswith('.pdf'):
                    story.append(Paragraph(f"Design PDF: {file_url}", styles['Normal']))
                else:
                    # Assume it's an image
                    response = requests.get(file_url)
                    response.raise_for_status()
                    image_data = BytesIO(response.content)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                        temp_file.write(image_data.getvalue())
                        temp_path = temp_file.name
                    
                    img = RLImage(temp_path, width=400, height=300)
                    story.append(img)
                    
                    os.unlink(temp_path)
            except Exception as e:
                story.append(Paragraph(f"Error loading design file: {str(e)}", styles['Normal']))
        
        story.append(Spacer(1, 24))

    doc.build(story)
    buffer.seek(0)
    return buffer


def create_pdf(design_ids):
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
