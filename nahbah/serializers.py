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
    contributor = ContributorSerializer()
    material = MaterialSerializer(read_only=True)
    material_id = CustomPrimaryKeyRelatedField(  # Use custom field
        source='material',
        queryset=Material.objects.all(),
        write_only=True,
        required=False
    )
    custom_material_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Design
        fields = "__all__"

    def validate(self, data):
        """
        Handle -1 as a custom material indicator.
        """
        material_id = data.get('material_id')
        custom_material_name = data.get('custom_material_name')

        if material_id == -1:
            if not custom_material_name:
                raise serializers.ValidationError(
                    {"custom_material_name": "Custom material name is required when selecting 'Other'."}
                )
            # Remove material_id since it's not a real PK
            data.pop('material_id', None)
        elif material_id is None and not custom_material_name:
            raise serializers.ValidationError(
                "Either a valid material_id or custom_material_name must be provided."
            )

        return data

    def create(self, validated_data):
        # Extract custom material if present
        custom_material_name = validated_data.pop('custom_material_name', None)
        if custom_material_name:
            material, created = Material.objects.get_or_create(name=custom_material_name)
            validated_data['material'] = material

        # Extract contributor data
        contributor_data = validated_data.pop("contributor", None)
        if contributor_data:
            email = contributor_data.get("email")
            contributor, created = Contributor.objects.get_or_create(email=email, defaults=contributor_data)
            validated_data["contributor"] = contributor

        return Design.objects.create(**validated_data)