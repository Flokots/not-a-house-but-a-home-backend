from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Design, Contributor, Material
import os


# Resource classes for import/export functionality
class DesignResource(resources.ModelResource):
    class Meta:
        model = Design
        fields = ('id', 'title', 'description', 'status', 'contributor__name', 'contributor__email', 'submission_date')


class ContributorResource(resources.ModelResource):
    class Meta:
        model = Contributor
        fields = ('id', 'name', 'email')


class MaterialResource(resources.ModelResource):
    class Meta:
        model = Material
        fields = ('id', 'name')


# Custom Admin Actions
def approve_designs(modeladmin, request, queryset):
    """Bulk approve selected designs"""
    updated = queryset.filter(status='pending').update(status='approved')
    messages.success(request, f'{updated} designs approved successfully!')


approve_designs.short_description = "Approve selected designs"


def reject_designs(modeladmin, request, queryset):
    """Bulk reject selected designs (requires individual rejection reasons)"""
    pending_designs = queryset.filter(status='pending')
    count = pending_designs.count()
    if count > 0:
        messages.warning(request,
                         f'{count} pending designs found. Please reject them individually to add rejection reasons.')
    else:
        messages.info(request, 'No pending designs to reject.')


reject_designs.short_description = "Reject selected designs (individual action required)"


# Enhanced Admin Classes
@admin.register(Design)
class DesignAdmin(ImportExportModelAdmin):
    resource_class = DesignResource

    list_display = [
        'title',
        'contributor',
        'material',
        'status_badge',
        'image_thumbnail',
        'submission_date'
    ]

    list_filter = [
        'status',
        'submission_date',
        'material',
        ('contributor', admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        'title',
        'description',
        'contributor__name',
        'contributor__email'
    ]

    readonly_fields = [
        'submission_date',
        'image_preview',
        'file_preview'
    ]

    fieldsets = (
        ('Design Information', {
            'fields': ('title', 'description', 'contributor', 'material')
        }),
        ('Files', {
            'fields': ('design_file', 'file_preview', 'preview_image', 'image_preview')
        }),
        ('Moderation', {
            'fields': ('status', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('submission_date',),
            'classes': ('collapse',)
        }),
    )

    actions = [approve_designs, reject_designs]

    def status_badge(self, obj):
        """Display status with color-coded badge"""
        colors = {
            'pending': '#ffc107',  # Warning yellow
            'approved': '#28a745',  # Success green
            'rejected': '#dc3545'  # Danger red
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.status.upper()
        )

    status_badge.short_description = 'Status'

    def image_thumbnail(self, obj):
        """Display small thumbnail of design preview image"""
        if obj.preview_image and hasattr(obj.preview_image, 'url'):
            try:
                return format_html(
                    '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                    obj.preview_image.url
                )
            except:
                return "Image error"
        return "No preview"

    image_thumbnail.short_description = 'Thumbnail'

    def image_preview(self, obj):
        """Display larger preview of design preview image"""
        if obj.preview_image and hasattr(obj.preview_image, 'url'):
            try:
                return format_html(
                    '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 4px;" />',
                    obj.preview_image.url
                )
            except:
                return "Image file error"
        return "No preview image uploaded"

    image_preview.short_description = 'Preview Image'

    def file_preview(self, obj):
        """Display design file info and download link"""
        if obj.design_file and hasattr(obj.design_file, 'url'):
            try:
                return format_html(
                    '<a href="{}" target="_blank" style="display: inline-block; padding: 8px 12px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px;">📄 View File</a>',
                    obj.design_file.url
                )
            except:
                return "File error"
        return "No design file uploaded"

    file_preview.short_description = 'Design File'

    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('contributor', 'material')


@admin.register(Contributor)
class ContributorAdmin(ImportExportModelAdmin):
    resource_class = ContributorResource

    list_display = [
        'name',
        'email',
        'design_count'
    ]

    search_fields = [
        'name',
        'email'
    ]

    def design_count(self, obj):
        """Count of contributor's designs"""
        count = obj.design_set.count()
        if count > 0:
            return format_html(
                '<a href="/admin/nahbah/design/?contributor__id__exact={}">{} designs</a>',
                obj.id, count
            )
        return "0 designs"

    design_count.short_description = 'Designs'


@admin.register(Material)
class MaterialAdmin(ImportExportModelAdmin):
    resource_class = MaterialResource

    list_display = [
        'name',
        'material_thumbnail',
        'design_count'
    ]

    search_fields = ['name']

    readonly_fields = [
        'material_preview'
    ]

    def material_thumbnail(self, obj):
        """Display small thumbnail of material image"""
        if obj.material_image and hasattr(obj.material_image, 'url'):
            try:
                return format_html(
                    '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                    obj.material_image.url
                )
            except:
                return "Image error"
        return "No image"

    material_thumbnail.short_description = 'Image'

    def material_preview(self, obj):
        """Display larger preview of material image"""
        if obj.material_image and hasattr(obj.material_image, 'url'):
            try:
                return format_html(
                    '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 4px;" />',
                    obj.material_image.url
                )
            except:
                return "Image file error"
        return "No image uploaded"

    material_preview.short_description = 'Image Preview'

    def design_count(self, obj):
        """Count of designs using this material"""
        count = obj.design_set.count()
        if count > 0:
            return format_html(
                '<a href="/admin/nahbah/design/?material__id__exact={}">{} designs</a>',
                obj.id, count
            )
        return "0 designs"

    design_count.short_description = 'Used in Designs'


# Customize admin site
admin.site.site_header = "Not A House But A Home - Admin"
admin.site.site_title = "NAHBAH Admin"
admin.site.index_title = "Welcome to NAHBAH Administration"

# Add View Site link
from django.conf import settings

admin.site.site_url = settings.FRONTEND_URL