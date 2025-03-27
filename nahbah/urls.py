from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContributorViewSet, DesignViewSet, MaterialViewSet

router = DefaultRouter()
router.register(r"materials", MaterialViewSet, basename="material")
router.register(r"designs", DesignViewSet, basename="design")
router.register(r"contributors", ContributorViewSet)

urlpatterns = router.urls
