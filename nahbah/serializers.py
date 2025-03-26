from rest_framework import serializers
from .models import Design, Material


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = "__all__"  # Include all fields


class DesignSerializer(serializers.ModelSerializer):
    material = MaterialSerializer(read_only=True)  # Nested material info
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(), write_only=True
    )  # Allow selecting a material via ID

    class Meta:
        model = Design
        fields = ["id", "title", "description", "material", "material_id", "design_file", "preview_image", "status",
                  "submission_date", "contributor"]
