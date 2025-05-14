from rest_framework import serializers
from .models import Contributor, Design, Material


class ContributorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contributor
        fields = ["name", "email"]


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = "__all__"  # Include all fields


class DesignSerializer(serializers.ModelSerializer):
    contributor = ContributorSerializer()  # Accept contributor details in the request
    material = MaterialSerializer(read_only=True)
    material_id = serializers.PrimaryKeyRelatedField(
        source='material',
        queryset=Material.objects.all(),
        write_only=True
    )
    custom_material_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Design
        fields = "__all__"

    def create(self, validated_data):
        # Extract custom material if present
        custom_material_name = validated_data.pop('custom_material_name', None)
        if custom_material_name:
            # Create a new material with just the name (no description)
            material, created = Material.objects.get_or_create(
                name=custom_material_name
            )
            validated_data['material'] = material
        # Extract contributor data
        contributor_data = validated_data.pop("contributor", None)

        # If contributor data is provided
        if contributor_data:
            email = contributor_data.get("email")

            # Check if contributor exists
            contributor, created = Contributor.objects.get_or_create(email=email, defaults=contributor_data)
            validated_data["contributor"] = contributor  # Link the existing/new contributor

            # Create Design instance
        return Design.objects.create(**validated_data)