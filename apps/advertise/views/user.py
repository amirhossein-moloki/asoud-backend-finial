from rest_framework import views, status, permissions
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.core.base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView
from apps.advertise.serializers import (
    AdvertiseSerializer,
    AdvertiseCreateSerializer,
    AdvertiseListSerializer,
)
from apps.advertise.models import (
    Advertisement,
    AdvImage,
    AdvKeyword
)
from apps.advertise.core import AdvertisementCore

# Create your views here.

class AdvertiseCreateView(BaseCreateView):
    """
    Create advertisement
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        return AdvertiseCreateSerializer
    
    def post(self, request):
        try:
            serialized_data = AdvertisementCore.create_advertisement(request)
            return self.success_response(data=serialized_data, message="Advertisement created successfully", code=201)
        except Exception as e:
            return self.error_response(f"Error creating advertisement: {str(e)}", 500)
        
class AdvertiseListView(BaseListView):
    """
    List advertisements with filtering
    """
    permission_classes = []
    
    def get_queryset(self):
        advertises = Advertisement.objects.filter(is_paid=True)

        if q := self.request.GET.get('q'):
            advertises = advertises.filter(name__icontains=q)
        
        if type := self.request.GET.get('type'):
            advertises = advertises.filter(type=type)

        if state := self.request.GET.get('state'):
            advertises = advertises.filter(state=state)
        
        if price_gt := self.request.GET.get('price_gt'):
            advertises = advertises.filter(price__gte=price_gt)

        if price_lt := self.request.GET.get('price_lt'):
            advertises = advertises.filter(price__lte=price_lt)

        return advertises
    
    def get_serializer_class(self):
        return AdvertiseListSerializer
    
    def get(self, request):
        advertises = self.get_queryset()
        serializer = AdvertiseListSerializer(advertises, many=True)
        return self.success_response(data=serializer.data)

class AdvertiseDetailView(BaseDetailView):
    """
    Retrieve advertisement details
    """
    permission_classes = []
    
    def get_queryset(self):
        return Advertisement.objects.all()
    
    def get_serializer_class(self):
        return AdvertiseSerializer
    
    def get(self, request, pk):
        try:
            advertise = Advertisement.objects.get(id=pk)
        except Advertisement.DoesNotExist:
            return self.error_response("Advertisement Not Found", 404)
        
        serializer = AdvertiseSerializer(advertise)
        return self.success_response(data=serializer.data)

class AdvertiseOwnListView(BaseListView):
    """
    List user's own advertisements
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Advertisement.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        return AdvertiseListSerializer
    
    def get(self, request):
        advertises = self.get_queryset()
        serializer = AdvertiseListSerializer(advertises, many=True)
        return self.success_response(data=serializer.data)

class AdvertiseUpdateView(BaseUpdateView):
    """
    Update advertisement
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Advertisement.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        return AdvertiseCreateSerializer
    
    def put(self, request, pk):
        try:
            advertise = Advertisement.objects.get(id=pk, user=request.user)
        except Advertisement.DoesNotExist:
            return self.error_response("Advertisement Not Found", 404)

        # remove extra fields from request before going to serializer
        data = [request.data.pop(key) for key in list(request.data.keys()) if key in ['product']]
        
        serializer = AdvertiseCreateSerializer(advertise, data=request.data, partial=True)
        if serializer.is_valid():
            obj = serializer.save()
            serialized_data = AdvertiseSerializer(obj).data
            return self.success_response(data=serialized_data)
        else:
            return self.error_response("Validation error", 400, str(serializer.errors))

class AdvertiseDeleteView(BaseDeleteView):
    """
    Delete advertisement
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Advertisement.objects.filter(user=self.request.user)
    
    def delete(self, request, pk):
        try:
            advertise = Advertisement.objects.get(id=pk, user=request.user)
        except Advertisement.DoesNotExist:
            return self.error_response("Advertisement Not Found", 404)

        advertise.delete()
        return self.success_response(message="Advertisement deleted successfully", code=204)

class AdvertisePaymentView(BaseDetailView):
    """
    Handle advertisement payment
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Advertisement.objects.all()
    
    def get_serializer_class(self):
        return AdvertiseSerializer
    
    def get(self, request):
        adv_id = request.GET.get('advertisement')

        if not adv_id:
            return self.error_response("Advertisement ID required", 400)

        try:
            advertise = Advertisement.objects.get(id=adv_id)
        except Advertisement.DoesNotExist:
            return self.error_response("Advertisement Not Found", 404)
        
        # Payment logic here
        serializer = AdvertiseSerializer(advertise)
        return self.success_response(data=serializer.data)

