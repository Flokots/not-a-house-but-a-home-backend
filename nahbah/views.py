from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Contributor, Design, Material
from .serializers import ContributorSerializer, DesignSerializer, MaterialSerializer
from django.shortcuts import get_object_or_404


class ContributorViewSet(viewsets.ModelViewSet):
    queryset = Contributor.objects.all()
    serializer_class = ContributorSerializer


# Material ViewSet (List Materials)
class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer


#  Design ViewSet (CRUD + Moderation)
class DesignViewSet(viewsets.ModelViewSet):
    queryset = Design.objects.all()
    serializer_class = DesignSerializer

    @action(detail=True, methods=["PATCH"])
    def moderate(self, request, pk=None):
        """Admins can approve or reject a design, but only if it is pending."""
        design = get_object_or_404(Design, pk=pk)

        if design.status != "pending":
            return Response(
                {"error": "This design has already been moderated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_status = request.data.get("status")
        if new_status not in ["approved", "rejected"]:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        # Handle rejection reason
        if new_status == "rejected":
            rejection_reason = request.data.get("rejection_reason", "").strip()
            if not rejection_reason:
                return Response(
                    {"error": "A rejection reason is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            design.rejection_reason = rejection_reason

        design.status = new_status
        design.save()

        return Response(
            {"message": f"Design {new_status} successfully!", "status": new_status}
        )

    @action(detail=True, methods=["PATCH"])
    def edit(self, request, pk=None):
        """Admins can edit design details before approving."""
        design = get_object_or_404(Design, pk=pk)

        if design.status != "pending":
            return Response(
                {"error": "Only pending designs can be edited."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DesignSerializer(design, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
