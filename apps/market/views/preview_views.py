from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import json

from ..models import Market, MarketSlider
from apps.product.models import Product


class MarketPreviewView(View):
    """
    Preview view for market owners to see how their store will look
    """
    
    def get(self, request, market_id):
        # Get market and ensure user owns it or is staff
        market = get_object_or_404(Market, id=market_id)
        
        if not (request.user.is_authenticated and 
                (market.owner == request.user or request.user.is_staff)):
            return render(request, 'market/preview_unauthorized.html', {
                'message': 'You are not authorized to preview this market.'
            })
        
        # Get market data
        slider_images = MarketSlider.objects.filter(market=market).order_by('created_at')
        products = Product.objects.filter(market=market, is_active=True)[:12]  # Limit for preview
        
        # Preview mode context
        context = {
            'market': market,
            'slider_images': slider_images,
            'products': products,
            'is_preview': True,
            'preview_mode': True,
            'can_edit': True,
        }
        
        return render(request, 'market/store_preview.html', context)


class MarketPreviewSettingsAPIView(APIView):
    """
    API view to update market preview settings
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, market_id):
        market = get_object_or_404(Market, id=market_id, owner=request.user)
        
        # Get settings from request
        settings_data = request.data.get('settings', {})
        
        # Update market theme settings
        if 'theme_color' in settings_data:
            market.theme_color = settings_data['theme_color']
        
        if 'background_color' in settings_data:
            market.background_color = settings_data['background_color']
        
        if 'text_color' in settings_data:
            market.text_color = settings_data['text_color']
        
        if 'show_products' in settings_data:
            market.show_products = settings_data['show_products']
        
        if 'show_slider' in settings_data:
            market.show_slider = settings_data['show_slider']
        
        market.save()
        
        return Response({
            'status': 'success',
            'message': 'Preview settings updated successfully',
            'settings': {
                'theme_color': getattr(market, 'theme_color', '#007bff'),
                'background_color': getattr(market, 'background_color', '#ffffff'),
                'text_color': getattr(market, 'text_color', '#333333'),
                'show_products': getattr(market, 'show_products', True),
                'show_slider': getattr(market, 'show_slider', True),
            }
        })
    
    def get(self, request, market_id):
        market = get_object_or_404(Market, id=market_id, owner=request.user)
        
        return Response({
            'settings': {
                'theme_color': getattr(market, 'theme_color', '#007bff'),
                'background_color': getattr(market, 'background_color', '#ffffff'),
                'text_color': getattr(market, 'text_color', '#333333'),
                'show_products': getattr(market, 'show_products', True),
                'show_slider': getattr(market, 'show_slider', True),
            }
        })


@method_decorator(csrf_exempt, name='dispatch')
class MarketPreviewModeToggleView(View):
    """
    Toggle preview mode for real-time editing
    """
    
    def post(self, request, market_id):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        market = get_object_or_404(Market, id=market_id, owner=request.user)
        
        try:
            data = json.loads(request.body)
            preview_mode = data.get('preview_mode', True)
            
            # Store preview mode in session
            request.session[f'preview_mode_{market_id}'] = preview_mode
            
            return JsonResponse({
                'status': 'success',
                'preview_mode': preview_mode,
                'message': f'Preview mode {"enabled" if preview_mode else "disabled"}'
            })
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)


class MarketLivePreviewAPIView(APIView):
    """
    Get live preview data for real-time updates
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, market_id):
        market = get_object_or_404(Market, id=market_id, owner=request.user)
        
        # Get fresh data
        slider_images = MarketSlider.objects.filter(market=market).order_by('created_at')
        products = Product.objects.filter(market=market, is_active=True)[:12]
        
        # Serialize data for JSON response
        slider_data = []
        for slider in slider_images:
            slider_data.append({
                'id': slider.id,
                'image_url': slider.image.url if slider.image else None,
                'title': getattr(slider, 'title', ''),
                'description': getattr(slider, 'description', ''),
            })
        
        product_data = []
        for product in products:
            product_data.append({
                'id': product.id,
                'title': product.title,
                'price': str(product.price) if product.price else '0',
                'image_url': product.image.url if product.image else None,
                'is_available': getattr(product, 'is_available', True),
            })
        
        return Response({
            'market': {
                'id': market.id,
                'title': market.title,
                'description': market.description,
                'logo_url': market.logo.url if market.logo else None,
                'background_url': market.background.url if market.background else None,
                'theme_color': getattr(market, 'theme_color', '#007bff'),
                'background_color': getattr(market, 'background_color', '#ffffff'),
                'text_color': getattr(market, 'text_color', '#333333'),
            },
            'slider_images': slider_data,
            'products': product_data,
            'stats': {
                'total_products': Product.objects.filter(market=market).count(),
                'active_products': Product.objects.filter(market=market, is_active=True).count(),
                'slider_count': slider_images.count(),
            }
        })


@login_required
def market_preview_iframe(request, market_id):
    """
    Iframe view for embedding preview in admin panel
    """
    market = get_object_or_404(Market, id=market_id)
    
    if not (market.owner == request.user or request.user.is_staff):
        return render(request, 'market/preview_unauthorized.html')
    
    # Get market data
    slider_images = MarketSlider.objects.filter(market=market).order_by('created_at')
    products = Product.objects.filter(market=market, is_active=True)[:8]  # Fewer for iframe
    
    context = {
        'market': market,
        'slider_images': slider_images,
        'products': products,
        'is_iframe': True,
        'is_preview': True,
    }
    
    return render(request, 'market/store_iframe.html', context)