from django.db import models


# List of possible models from dropdown selection
class Material(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


# Contributor information (Optional)
class Contributor(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name if self.name else "Anonymous"


# Design Submission Model
class Design(models.Model):
    title = models.CharField(max_length=255)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    description = models.TextField(max_length=1500)
    pdf_file = models.FileField(upload_to="designs/pdfs", blank=True, null=True)
    image_file = models.ImageField(upload_to="designs/images", blank=True, null=True)
    contributor = models.ForeignKey(Contributor, on_delete=models.SET_NULL, blank=True, null=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending"
    )

    def __str__(self):
        return self.title