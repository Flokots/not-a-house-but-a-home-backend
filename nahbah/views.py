from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Design, Material
from .serializers import DesignSerializer, MaterialSerializer
from django.shortcuts import get_object_or_404


# Material ViewSet (List Materials)
class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer


#  Design ViewSet (CRUD + Moderation)
class DesignViewSet(viewsets.ModelViewSet):
    queryset = Design.objects.all()
    serializer_class = DesignSerializer

    # Approve or Reject a Design
    @action(detail=True, methods=["PATCH"])
    def moderate(self, request, pk=None):
        """Admin can approve or reject a design, but only if it is pending."""
        design = get_object_or_404(Design, pk=pk)

        # ✅ Prevent moderation of already approved/rejected designs
        if design.status != "pending":
            return Response(
                {"error": "This design has already been moderated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_status = request.data.get("status")
        if new_status not in ["approved", "rejected"]:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        design.status = new_status
        design.save()
        return Response({"message": f"Design {new_status} successfully!"})

    #  Edit Design Before Approval
    @action(detail=True, methods=["PATCH"])
    def edit(self, request, pk=None):
        """Admins can edit design details before approving."""
        design = get_object_or_404(Design, pk=pk)
        serializer = DesignSerializer(design, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
