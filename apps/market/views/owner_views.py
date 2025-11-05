from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
import json
from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from utils.response import ApiResponse

from apps.market.models import (
    Market,
    MarketLocation,
    MarketContact,
    MarketSlider,
    MarketTheme,
)

from apps.market.serializers.owner_serializers import (
    MarketCreateSerializer,
    MarketUpdateSerializer,
    MarketLocationCreateSerializer,
    MarketLocationUpdateSerializer,
    MarketContactCreateSerializer,
    MarketContactUpdaterSerializer,
    MarketListSerializer,
    MarketSliderListSerializer,
    MarketThemeCreateSerializer,
)


from utils.error_handlers import ErrorHandlerMixin, create_error_response, handle_validation_errors
from utils.logging_config import log_error, log_info, log_user_action

from ..models import Market, MarketLocation
from ..serializers.owner_serializers import (
    MarketCreateSerializer,
    MarketGetSerializer,
    MarketListSerializer,
    MarketLocationCreateSerializer,
    MarketLocationSerializer,
    MarketLocationUpdateSerializer,
    MarketUpdateSerializer,
)


class MarketCreate(ErrorHandlerMixin, APIView):
    """
    ایجاد مارکت جدید با مدیریت خطا و لاگینگ پیشرفته
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MarketCreateSerializer(data=request.data, context={'request': request})
        
        try:
            with transaction.atomic():
                if serializer.is_valid():
                    market = serializer.save(user=request.user)
                    
                    log_user_action(
                        request.user,
                        'CREATE_MARKET',
                        model_name='Market',
                        object_id=market.id,
                        details={'market_name': market.name}
                    )
                    
                    log_info(f"Market '{market.name}' created successfully.", user=request.user)
                    
                    return Response({
                        'success': True,
                        'message': 'Market created successfully',
                        'data': MarketGetSerializer(market).data
                    }, status=status.HTTP_201_CREATED)
                
                return Response(handle_validation_errors(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            log_error(e, context={'request_data': request.data}, user=request.user)
            return create_error_response(e, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketUpdate(ErrorHandlerMixin, APIView):
    """
    آپدیت مارکت با لاگینگ و خطایابی
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        market = get_object_or_404(Market, pk=pk, user=self.request.user)
        return market

    def put(self, request, pk):
        try:
            market = self.get_object(pk)
            serializer = MarketUpdateSerializer(market, data=request.data, context={'request': request})

            if serializer.is_valid():
                with transaction.atomic():
                    updated_market = serializer.save()
                    
                    log_user_action(
                        request.user,
                        'UPDATE_MARKET',
                        model_name='Market',
                        object_id=updated_market.id,
                        details={'updated_fields': list(request.data.keys())}
                    )
                    
                    log_info(f"Market '{updated_market.name}' updated successfully.", user=request.user)
                    
                    return Response({
                        'success': True,
                        'message': 'Market updated successfully',
                        'data': MarketGetSerializer(updated_market).data
                    })
            
            return Response(handle_validation_errors(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            log_error(e, context={'market_id': pk, 'request_data': request.data}, user=request.user)
            return create_error_response(e)


class MarketGet(ErrorHandlerMixin, generics.RetrieveAPIView):
    """
    دریافت اطلاعات یک مارکت
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MarketGetSerializer
    queryset = Market.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class MarketList(ErrorHandlerMixin, generics.ListAPIView):
    """
    لیست مارکت‌های کاربر
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MarketListSerializer

    def get_queryset(self):
        return Market.objects.filter(user=self.request.user).order_by('-created_at')


class MarketLocationCreate(ErrorHandlerMixin, APIView):
    """
    ایجاد موقعیت مکانی برای مارکت
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MarketLocationCreateSerializer(data=request.data, context={'request': request})
        
        try:
            if serializer.is_valid():
                market = serializer.validated_data['market']
                
                # Check ownership
                if market.user != request.user:
                    return create_error_response(PermissionError('You do not own this market.'), status_code=status.HTTP_403_FORBIDDEN)
                
                # Prevent duplicate location
                if MarketLocation.objects.filter(market=market).exists():
                    return create_error_response(BusinessLogicError('Location for this market already exists.'), status_code=status.HTTP_400_BAD_REQUEST)

                with transaction.atomic():
                    location = serializer.save()
                    log_user_action(request.user, 'CREATE_MARKET_LOCATION', 'MarketLocation', location.id)
                    log_info(f"Location created for market '{market.name}'", user=request.user)
                    
                    return Response({
                        'success': True,
                        'message': 'Market location created successfully',
                        'data': MarketLocationCreateSerializer(location).data
                    }, status=status.HTTP_201_CREATED)
            
            return Response(handle_validation_errors(serializer.errors), status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            log_error(e, context={'request_data': request.data}, user=request.user)
            return create_error_response(e)


class MarketLocationUpdate(ErrorHandlerMixin, APIView):
    """
    آپدیت موقعیت مکانی مارکت
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        location = get_object_or_404(MarketLocation, pk=pk)
        if location.market.user != self.request.user:
            raise PermissionError('You do not have permission to edit this location.')
        return location

    def put(self, request, pk):
        try:
            location = self.get_object(pk)
            serializer = MarketLocationUpdateSerializer(location, data=request.data, context={'request': request})

            if serializer.is_valid():
                with transaction.atomic():
                    updated_location = serializer.save()
                    log_user_action(request.user, 'UPDATE_MARKET_LOCATION', 'MarketLocation', updated_location.id)
                    log_info(f"Location updated for market '{location.market.name}'", user=request.user)
                    
                    return Response({
                        'success': True,
                        'message': 'Market location updated successfully',
                        'data': MarketLocationUpdateSerializer(updated_location).data
                    })
            
            return Response(handle_validation_errors(serializer.errors), status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            log_error(e, context={'location_id': pk, 'request_data': request.data}, user=request.user)
            return create_error_response(e)


class MarketLocationGetAPIView(generics.RetrieveAPIView):
    serializer_class = MarketLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MarketLocation.objects.filter(market__user=self.request.user)


class MarketContactCreateAPIView(views.APIView):
    def post(self, request):
        serializer = MarketContactCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        
        if serializer.is_valid(raise_exception=True):
            market_contact = serializer.save()

            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    **serializer.data,
                },
                message='Market contact created successfully.',
            )

            return Response(success_response, status=status.HTTP_201_CREATED)

        response = ApiResponse(
            success=False,
            code=500,
            error={
                'code': 'server_error',
                'detail': 'Server error',
            }
        )

        return Response(response, status=status.HTTP_200_OK)


@method_decorator(login_required, name='dispatch')
class MarketPersonalizationInterfaceView(TemplateView):
    """
    View for the store personalization interface
    """
    template_name = 'market/personalization_interface.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        market_id = kwargs.get('pk')
        
        try:
            market = get_object_or_404(Market, id=market_id, owner=self.request.user)
            context['market'] = market
            
            # Get existing theme if available
            try:
                theme = MarketTheme.objects.get(market=market)
                context['theme'] = theme
            except MarketTheme.DoesNotExist:
                context['theme'] = None
                
            # Get existing sliders
            sliders = MarketSlider.objects.filter(market=market)
            context['sliders'] = sliders
            
        except Market.DoesNotExist:
            context['error'] = 'Market not found or you do not have permission to edit it.'
            
        return context


class MarketContactUpdateAPIView(views.APIView):
    def put(self, request, pk):
        try:
            market = Market.objects.get(id=pk)
            market_contact = MarketContact.objects.get(market=market)

        except Market.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_not_found',
                    'detail': 'Market not found in the database',
                }
            )
            return Response(response)

        except MarketContact.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_contact_not_found',
                    'detail': 'Market contact not found in the database',
                }
            )
            return Response(response)

        serializer = MarketContactUpdaterSerializer(
            market_contact,
            data=request.data,
            partial=True,
            context={'request': request},
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            success_response = ApiResponse(
                success=True,
                code=200,
                data=serializer.data,
                message='Market contact updated successfully.',
            )
            return Response(success_response, status=status.HTTP_200_OK)

class MarketContactGetAPIView(views.APIView):
    def get(self, request, pk, format=None):
        try:
            market = Market.objects.get(id=pk)
            market_contact = MarketContact.objects.get(market=market)

        except Market.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_not_found',
                    'detail': 'Market not found in the database',
                }
            )
            return Response(response)

        except MarketContact.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_contact_not_found',
                    'detail': 'Market contact not found in the database',
                }
            )
            return Response(response)

        serializer = MarketContactUpdaterSerializer(
            market_contact,
            context={'request': request},
        )

        success_response = ApiResponse(
            success=True,
            code=200,
            data=serializer.data,
            message='Data retrieved successfully.',
        )
        return Response(success_response, status=status.HTTP_200_OK)


class MarketInactiveAPIView(views.APIView):
    def get(self, request, pk, format=None):
        try:
            market_obj = Market.objects.get(
                id=pk,
            )
        except Market.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_not_found',
                    'detail': 'Market not found in the database',
                }
            )
            return Response(response)

        market_obj.status = "inactive"
        market_obj.save()

        success_response = ApiResponse(
            success=True,
            code=200,
            data={},
            message='Market inactivated successfully'
        )

        return Response(success_response)


class MarketQueueAPIView(views.APIView):
    def get(self, request, pk, format=None):
        try:
            market_obj = Market.objects.get(
                id=pk,
            )
        except Market.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_not_found',
                    'detail': 'Market not found in the database',
                }
            )
            return Response(response)

        market_obj.status = "queue"
        market_obj.save()

        success_response = ApiResponse(
            success=True,
            code=200,
            data={},
            message='Market queued successfully'
        )

        return Response(success_response)


class MarketLogoAPIView(views.APIView):
    def post(self, request, pk):
        logo_img = request.FILES.get('logo_img')

        try:
            market_obj = Market.objects.get(
                id=pk,
            )
        except Market.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_not_found',
                    'detail': 'Market not found in the database',
                }
            )
            return Response(response)

        market_obj.logo_img = logo_img
        market_obj.save()

        data = {
            'logo_img': request.build_absolute_uri(market_obj.logo_img.url),
        }

        success_response = ApiResponse(
            success=True,
            code=200,
            data=data,
            message='Logo modified successfully'
        )

        return Response(success_response)

    def delete(self, request, pk):
        try:
            market_obj = Market.objects.get(id=pk)
        except Market.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_not_found',
                    'detail': 'Market not found in the database',
                }
            )
            return Response(response)

        # Delete the logo_img file
        if market_obj.logo_img:
            market_obj.logo_img.delete(save=True)

        # Clear the reference to the logo_img in the model
        market_obj.logo_img = None
        market_obj.save()

        success_response = ApiResponse(
            success=True,
            code=200,
            data={},
            message='Logo removed successfully',
        )

        return Response(success_response)


class MarketBackgroundAPIView(views.APIView):
    def post(self, request, pk):
        background_img = request.FILES.get('background_img')

        try:
            market_obj = Market.objects.get(
                id=pk,
            )
        except Market.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_not_found',
                    'detail': 'Market not found in the database',
                }
            )
            return Response(response)

        market_obj.background_img = background_img
        market_obj.save()

        data = {
            'background_img': request.build_absolute_uri(market_obj.background_img.url),
        }

        success_response = ApiResponse(
            success=True,
            code=200,
            data=data,
            message='Background modified successfully'
        )

        return Response(success_response)

    def delete(self, request, pk):
        try:
            market_obj = Market.objects.get(id=pk)
        except Market.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_not_found',
                    'detail': 'Market not found in the database',
                }
            )
            return Response(response)

        # Delete the logo_img file
        if market_obj.background_img:
            market_obj.background_img.delete(save=True)

        # Clear the reference to the logo_img in the model
        market_obj.background_img = None
        market_obj.save()

        success_response = ApiResponse(
            success=True,
            code=200,
            data={},
            message='Background removed successfully',
        )

        return Response(success_response)


class MarketSliderAPIView(views.APIView):
    def get(self, request, pk):
        try:
            market_obj = Market.objects.get(id=pk)

        except Market.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_not_found',
                    'detail': 'Market not found in the database',
                }
            )
            return Response(response)

        slider_list = MarketSlider.objects.filter(
            market=market_obj,
        )

        serializer = MarketSliderListSerializer(
            slider_list,
            many=True,
            context={"request": request},
        )

        success_response = ApiResponse(
            success=True,
            code=200,
            data=serializer.data,
            message='Data retrieved successfully'
        )

        return Response(success_response)

    def post(self, request, pk):
        slider_img = request.FILES.get('slider_img')

        try:
            market_obj = Market.objects.get(
                id=pk,
            )
        except Market.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_not_found',
                    'detail': 'Market not found in the database',
                }
            )
            return Response(response)

        market_slider_img = MarketSlider.objects.create(
            market=market_obj,
            image=slider_img,
        )

        data = {
            'slider_img': request.build_absolute_uri(market_slider_img.image.url),
        }

        success_response = ApiResponse(
            success=True,
            code=200,
            data=data,
            message='New slider has been created successfully'
        )

        return Response(success_response)

    def delete(self, request, pk):
        try:
            market_slider_obj = MarketSlider.objects.get(id=pk)
        except MarketSlider.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_slider_not_found',
                    'detail': 'MarketSlider not found in the database',
                }
            )
            return Response(response)

        # Delete the file
        market_slider_obj.delete()

        success_response = ApiResponse(
            success=True,
            code=200,
            data={},
            message='MarketSlider removed successfully',
        )

        return Response(success_response)

    def patch(self, request, pk):
        try:
            market_slider_obj = MarketSlider.objects.get(id=pk)
        except MarketSlider.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'market_slider_not_found',
                    'detail': 'MarketSlider not found in the database',
                }
            )
            return Response(response)

        # Update the image if provided in the request
        slider_img = request.FILES.get('slider_img')
        if slider_img:
            market_slider_obj.image = slider_img

        market_slider_obj.save()

        data = {
            'slider_img': request.build_absolute_uri(market_slider_obj.image.url),
        }

        success_response = ApiResponse(
            success=True,
            code=200,
            data=data,
            message='MarketSlider updated successfully'
        )

        return Response(success_response, status=status.HTTP_200_OK)


class MarketThemeAPIView(views.APIView):
    def post(self, request, pk):    
        try:
            market = Market.objects.get(id=pk)
            market_theme = MarketTheme.objects.get(market=market)
            serializer = MarketThemeCreateSerializer(
                market_theme,
                data=request.data,
                context={'request': request},
            )

        except MarketTheme.DoesNotExist:
            serializer = MarketThemeCreateSerializer(
                data=request.data,
                context={'request': request},
            )
        
        except Market.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Market Not Found"
                )
            )

        if serializer.is_valid(raise_exception=True):
            serializer.save(
                market=market,
            )

            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    **serializer.data,
                },
                message='Market theme created successfully.',
            )

            return Response(success_response, status=status.HTTP_201_CREATED)

        response = ApiResponse(
            success=False,
            code=500,
            error={
                'code': 'server_error',
                'detail': 'Server error',
            }
        )

        return Response(response, status=status.HTTP_200_OK)
