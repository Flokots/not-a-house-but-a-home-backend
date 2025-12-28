import json
from rest_framework import serializers
from .models import Contributor, Design, Material
from cloudinary.utils import cloudinary_url


class ContributorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contributor
        fields = ["name", "email"]


class MaterialSerializer(serializers.ModelSerializer):
    material_image_url = serializers.SerializerMethodField()  # Add this

    class Meta:
        model = Material
        fields = "__all__"

    def get_material_image_url(self, obj):
        if obj.material_image:
            return cloudinary_url(obj.material_image.public_id)[0]  # Full URL
        return None


class CustomPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """
    Custom field that allows -1 as a special value without validating it as a PK.
    """
    def to_internal_value(self, data):
        if data == -1 or str(data) == '-1':
            return -1  # Skip validation for -1
        return super().to_internal_value(data)


class DesignSerializer(serializers.ModelSerializer):
    contributor = serializers.JSONField(write_only=True)  # Accept JSON string
    material = MaterialSerializer(read_only=True)
    material_id = CustomPrimaryKeyRelatedField(  # Use custom field
        source='material',
        queryset=Material.objects.all(),
        write_only=True,
        required=False
    )
    custom_material_name = serializers.CharField(write_only=True, required=False)
    design_file = serializers.FileField(required=False, allow_null=True)
    preview_image = serializers.SerializerMethodField()

    class Meta:
        model = Design
        fields = ['id', 'title', 'description', 'design_file', 'preview_image', 'material', 'material_id', 'custom_material_name',
                  'contributor', 'submission_date', 'status', 'rejection_reason']

    def get_preview_image(self, obj):
        """
        Return preview image URL.
        Priority:
        1. If preview_image field has a manually uploaded file, return it
        2. Otherwise, generate from design_file using Cloudinary transformations
        """
        # If admin uploaded a custom preview, use that
        if obj.preview_image:
            return str(obj.preview_image.url)
        
        # Otherwise, generate from design_file
        if obj.design_file:
            return obj.get_preview_url()
        
        return None
    
    def validate(self, data):
        """
        Handle -1 as a custom material indicator.
        """
        material = data.get('material')  # Changed from 'material_id' to 'material'
        custom_material_name = data.get('custom_material_name')

        if material == -1:
            if not custom_material_name:
                raise serializers.ValidationError(
                    {"custom_material_name": "Custom material name is required when selecting 'Other'."}
                )
            # Remove material since it's not a real object
            data.pop('material', None)  # Changed from 'material_id'
        elif material is None and not custom_material_name:
            raise serializers.ValidationError(
                "Either a valid material_id or custom_material_name must be provided."
            )

        return data

    def create(self, validated_data):
        # Handle custom material
        custom_material_name = validated_data.pop('custom_material_name', None)
        if custom_material_name:
            material, created = Material.objects.get_or_create(name=custom_material_name)
            validated_data['material'] = material

        # Parse contributor JSON string
        contributor_data = validated_data.pop("contributor", None)
        if contributor_data:
            # If it's a string, parse it
            if isinstance(contributor_data, str):
                contributor_data = json.loads(contributor_data)
            
            email = contributor_data.get("email")
            contributor, created = Contributor.objects.get_or_create(
                email=email, 
                defaults={"name": contributor_data.get("name")}
            )
            validated_data["contributor"] = contributor

        return Design.objects.create(**validated_data)