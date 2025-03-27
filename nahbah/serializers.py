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
    material = serializers.PrimaryKeyRelatedField(queryset=Material.objects.all())  # Expect material ID
    contributor = ContributorSerializer()  # Accept contributor details in the request

    class Meta:
        model = Design
        fields = "__all__"

    def create(self, validated_data):
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