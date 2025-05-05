import tempfile

import fitz
import os
import re
from io import BytesIO

from PIL import Image
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import models
from django_resized import ResizedImageField
from pdf2image import convert_from_path


# List of possible models from dropdown selection
class Material(models.Model):
    name = models.CharField(max_length=255, unique=True)
    material_image = ResizedImageField(size=[300, 300], upload_to='materials/', blank=True, null=True)

    def __str__(self):
        return self.name


# Contributor information (Optional)
class Contributor(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name if self.name else "Anonymous"


def validate_file_size(file):
    max_size_mb = 5
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File size must not exceed {max_size_mb} MB.")


def validate_file_type(file):
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError("Unsupported file type. Only PDF or image files are allowed.")


# Design Submission Model
class Design(models.Model):
    title = models.CharField(max_length=255)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    description = models.TextField(max_length=1500)
    design_file = models.FileField(upload_to="designs/", blank=True, null=True,
                                   validators=[validate_file_size, validate_file_type],
                                   help_text="Upload a PDF or an image (max 5MB)")
    preview_image = models.ImageField(upload_to="previews/", blank=True, null=True)
    contributor = models.ForeignKey(Contributor, on_delete=models.SET_NULL, blank=True, null=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending"
    )
    rejection_reason = models.TextField(blank=True, null=True)

    def _sanitize_pdf(self, pdf_path):
        """Re-saves PDF after removing potentially unsafe objects."""
        try:
            doc = fitz.open(pdf_path)
            clean_path = pdf_path.replace(".pdf", "_clean.pdf")
            doc.save(clean_path, garbage=4, deflate=True)
            doc.close()

            # Replace original file with sanitized one
            with open(clean_path, "rb") as f:
                self.design_file.save(os.path.basename(clean_path), File(f), save=False)
        except Exception as e:
            print(f"PDF sanitization failed: {e}")

    def _sanitize_image(self, img_path):
        try:
            print(f"Sanitizing image: {img_path}")
            with Image.open(img_path) as img:
                # Remove EXIF by re-saving
                rgb_image = img.convert("RGB")
                rgb_image.save(img_path, format="JPEG", quality=90)
        except Exception as e:
            print(f"Image sanitization failed: {e}")

    def save(self, *args, **kwargs):
        is_new_file = self.pk is None or "design_file" in kwargs.get("update_fields", []) or not self.preview_image

        super().save(*args, **kwargs)  # Save instance first

        if self.design_file and is_new_file:
            file_extension = os.path.splitext(self.design_file.name)[-1].lower()
            file_path = self.design_file.path  # Get full path safely

            if default_storage.exists(file_path):  # Ensure file exists before processing
                try:
                    if file_extension == ".pdf":
                        self._sanitize_pdf(file_path)
                        self._generate_preview_from_pdf(file_path)
                    elif file_extension in [".jpg", ".jpeg", ".png"]:
                        self._sanitize_image(file_path)
                        self._generate_preview_from_image(file_path)
                except Exception as e:
                    print(f"Error processing file {self.design_file.name}: {e}")

    def _generate_preview_from_pdf(self, pdf_path):
        """Extract the first page of a PDF and save as preview image."""
        print(f"Generating preview for PDF: {pdf_path}")
        with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(pdf_path, first_page=1, last_page=1)
            if images:
                img_io = BytesIO()
                images[0].save(img_io, format="JPEG", quality=100)
                img_content = ContentFile(img_io.getvalue(), name=f"preview_{self.pk}.jpg")

                print(f"Saving preview image: {img_content.name}")
                self.preview_image.save(img_content.name, img_content, save=True)

    def _generate_preview_from_image(self, img_path):
        """Resize uploaded image and save it as a preview with a meaningful name."""
        print(f"Generating preview for image: {img_path}")
        with Image.open(img_path) as img:
            img.thumbnail((300, 300))  # Resize while maintaining aspect ratio

            # Create a clean filename based on the title
            base_name = re.sub(r'[^a-zA-Z0-9]+', '_', self.title.lower()).strip('_')  # Remove special characters
            base_name = base_name[:50]  # Truncate if too long

            preview_filename = f"{base_name}_{self.pk}.png"  # Ensure uniqueness

            preview_io = BytesIO()
            img.save(preview_io, format="PNG", quality=100)  # Save as PNG
            preview_content = ContentFile(preview_io.getvalue(), name=preview_filename)

            print(f"Saving preview image: {preview_filename}")
            self.preview_image.save(preview_filename, preview_content, save=True)

    def __str__(self):
        return self.title
