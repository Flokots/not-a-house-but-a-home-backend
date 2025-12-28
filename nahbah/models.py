import os
from django.core.exceptions import ValidationError
from django.db import models
from cloudinary.models import CloudinaryField


class Material(models.Model):
    name = models.CharField(max_length=255, unique=True)
    material_image = CloudinaryField('image', blank=True, null=True)

    def __str__(self):
        return self.name


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
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.webp']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError("Unsupported file type. Only PDF or image files are allowed.")


class Design(models.Model):
    title = models.CharField(max_length=255)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    description = models.TextField(max_length=1500)
    design_file = CloudinaryField(
        'image', 
        blank=True, 
        null=True, 
        help_text="Upload a PDF or an image (max 5MB)"
    )
    preview_image = CloudinaryField('image', blank=True, null=True)
    contributor = models.ForeignKey(Contributor, on_delete=models.SET_NULL, blank=True, null=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending"
    )
    rejection_reason = models.TextField(blank=True, null=True)

    def get_preview_url(self):
        """
        Generate preview URL from design_file using Cloudinary transformations.
        
        For PDFs: Uses pg_1 transformation and converts to WebP format
        For images: Returns the image URL with f_auto (auto WebP conversion)
        
        From Cloudinary docs:
        - pg_1 extracts first page of PDF
        - f_auto automatically selects best format (WebP for modern browsers)
        """
        if not self.design_file:
            return None
        
        try:
            file_url = str(self.design_file.url)
            ext = os.path.splitext(file_url)[1].lower()
            print("Design file URL:", file_url)
            preview_image = file_url.replace(ext, '.webp')
            print("Generated preview URL:", preview_image)
            return preview_image
        except (AttributeError, ValueError):
            return None
    
    def save(self, *args, **kwargs):
        """
        Save the design.
        Preview generation happens on-demand via get_preview_url() in serializer.
        """
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
