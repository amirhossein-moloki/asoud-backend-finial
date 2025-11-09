from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from apps.base.permissions import IsOwner
from apps.item.models import Item
from apps.item.serializers import ItemSerializer

class ItemViewSet(viewsets.ModelViewSet):
    """
    Viewset for item registration and management
    """
    parser_classes = (MultiPartParser, FormParser)
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Item.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def publish(self, request, *args, **kwargs):
        """Publish an item"""
        item = self.get_object()
        item.status = Item.PENDING_APPROVAL
        item.save()
        return Response({'status': 'item submitted for approval'})

    @action(detail=True, methods=['post'])
    def unpublish(self, request, *args, **kwargs):
        """Unpublish an item"""
        item = self.get_object()
        item.status = Item.NOT_PUBLISHED
        item.save()
        return Response({'status': 'item unpublished'})

    @action(detail=True, methods=['post'])
    def save_for_editing(self, request, *args, **kwargs):
        """Save item for later editing"""
        item = self.get_object()
        item.status = Item.NEEDS_EDITING
        item.save()
        return Response({'status': 'item saved for revision'})

    @action(detail=True, methods=['post'])
    def activate(self, request, *args, **kwargs):
        """Activate an item"""
        item = self.get_object()
        item.status = Item.PUBLISHED
        item.save()
        return Response({'status': 'item activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, *args, **kwargs):
        """Deactivate an item"""
        item = self.get_object()
        item.status = Item.INACTIVE
        item.save()
        return Response({'status': 'item deactivated'})