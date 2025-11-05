from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

# Import base utilities with fallback
try:
    from apps.base.utils import ApiResponse
except ImportError:
    # Fallback ApiResponse if not available
    class ApiResponse:
        def __init__(self, success=True, code=200, data=None, message='', error=None):
            self.success = success
            self.code = code
            self.data = data or {}
            self.message = message
            self.error = error or {}

# Import models with correct paths
try:
    from ..models.office_registration_models import Market, MarketLocation, MarketContact, MarketSchedule
except ImportError:
    try:
        from .models import Market, MarketLocation, MarketContact, MarketSchedule
    except ImportError:
        Market = MarketLocation = MarketContact = MarketSchedule = None

# Import serializers with correct paths
try:
    from ..serializers.office_registration_serializers import (
        MarketCreateSerializer, MarketLocationCreateSerializer, MarketContactCreateSerializer,
        PaymentGatewaySerializer, SubscriptionFeeCalculatorSerializer, SubscriptionPaymentSerializer,
        IntegratedMarketCreateSerializer
    )
except ImportError:
    try:
        from .serializers import (
            MarketCreateSerializer, MarketLocationCreateSerializer, MarketContactCreateSerializer,
            PaymentGatewaySerializer, SubscriptionFeeCalculatorSerializer, SubscriptionPaymentSerializer,
            IntegratedMarketCreateSerializer
        )
    except ImportError:
        # Fallback serializers if not available
        MarketCreateSerializer = MarketLocationCreateSerializer = MarketContactCreateSerializer = None
        PaymentGatewaySerializer = SubscriptionFeeCalculatorSerializer = SubscriptionPaymentSerializer = None
        IntegratedMarketCreateSerializer = None

# Import related models with fallbacks
try:
    from apps.category.models import SubCategory
except ImportError:
    try:
        from ..models.category_models import SubCategory
    except ImportError:
        SubCategory = None

try:
    from apps.location.models import City, Province, Country
except ImportError:
    City = Province = Country = None

try:
    from apps.discount.models import Discount
except ImportError:
    Discount = None

try:
    from apps.wallet.models import Wallet, Transaction
except ImportError:
    Wallet = Transaction = None

# Import error handling utilities
try:
    from ..utils.error_handlers import (
        ErrorHandlerMixin, log_error, log_info, log_warning,
        ValidationError, BusinessLogicError, PaymentError,
        create_error_response, handle_validation_errors
    )
except ImportError:
    # Fallback error handling
    class ErrorHandlerMixin:
        pass
    
    def log_error(error, context=None, user=None):
        logging.error(f"Error: {error}")
    
    def log_info(message, context=None, user=None):
        logging.info(f"Info: {message}")
    
    def log_warning(message, context=None, user=None):
        logging.warning(f"Warning: {message}")
    
    class ValidationError(Exception):
        pass
    
    class BusinessLogicError(Exception):
        pass
    
    class PaymentError(Exception):
        pass
    
    def create_error_response(error, status_code=400):
        return Response({'error': str(error)}, status=status_code)
    
    def handle_validation_errors(errors):
        return {'success': False, 'errors': errors}

try:
    from ..utils.logging_config import log_user_action, log_payment_transaction, log_security_event
except ImportError:
    # Fallback logging functions
    def log_user_action(user, action, model_name=None, object_id=None, details=None):
        logging.info(f"User {user} performed {action} on {model_name}:{object_id}")
    
    def log_payment_transaction(transaction_data):
        logging.info(f"Payment transaction: {transaction_data}")
    
    def log_security_event(event_type, user=None, ip_address=None, details=None):
        logging.warning(f"Security event: {event_type}")

# Configure logger
logger = logging.getLogger('office_registration')


class MarketCreateAPIView(ErrorHandlerMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Log the request
            log_info("Market creation request received", 
                    context={'user_id': request.user.id}, 
                    user=request.user)
            
            serializer = MarketCreateSerializer(data=request.data)
            
            if not serializer.is_valid():
                log_warning("Market creation validation failed", 
                           context={'errors': serializer.errors}, 
                           user=request.user)
                return Response(handle_validation_errors(serializer.errors), 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # بررسی مالکیت
            if not request.user.is_authenticated:
                log_security_event("Unauthenticated market creation attempt", 
                                 ip_address=request.META.get('REMOTE_ADDR'))
                return Response(
                    ApiResponse(
                        success=False,
                        code=401,
                        error={'code': 'authentication_required', 'detail': 'Authentication required'}
                    ),
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # ایجاد Market with transaction
            with transaction.atomic():
                market = serializer.save(user=request.user)
                
                # Log successful creation
                log_user_action(request.user, 'CREATE', 'Market', market.id, 
                              {'business_id': market.business_id, 'name': market.name})
                
                log_info("Market created successfully", 
                        context={'market_id': market.id, 'business_id': market.business_id}, 
                        user=request.user)
            
            success_response = ApiResponse(
                success=True,
                code=201,
                data={
                    'market_id': market.id,
                    'business_id': market.business_id,
                    'name': market.name,
                    'template': market.template,
                    'next_step': 'location'
                },
                message='Market created successfully.',
            )
            
            return Response(success_response, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            log_error(e, context={'request_data': request.data}, user=request.user)
            return create_error_response(e, status.HTTP_400_BAD_REQUEST)
        except BusinessLogicError as e:
            log_error(e, context={'request_data': request.data}, user=request.user)
            return create_error_response(e, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            log_error(e, context={'request_data': request.data, 'view': 'MarketCreateAPIView'}, user=request.user)
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketLocationCreateAPIView(ErrorHandlerMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            log_info("Market location creation request received", 
                    context={'user_id': request.user.id}, 
                    user=request.user)
            
            serializer = MarketLocationCreateSerializer(data=request.data)
            
            if not serializer.is_valid():
                log_warning("Market location validation failed", 
                           context={'errors': serializer.errors}, 
                           user=request.user)
                return Response(handle_validation_errors(serializer.errors), 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # بررسی مالکیت Market
            market_id = serializer.validated_data.get('market')
            try:
                market = Market.objects.get(id=market_id, user=request.user)
            except Market.DoesNotExist:
                log_security_event("Unauthorized market access attempt", 
                                 user=request.user, 
                                 details={'market_id': market_id})
                return Response(
                    ApiResponse(
                        success=False,
                        code=404,
                        error={'code': 'market_not_found', 'detail': 'Market not found or access denied'}
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # ایجاد MarketLocation with transaction
            with transaction.atomic():
                location = serializer.save()
                
                log_user_action(request.user, 'CREATE', 'MarketLocation', location.id, 
                              {'market_id': market.id, 'city': location.city.name})
                
                log_info("Market location created successfully", 
                        context={'location_id': location.id, 'market_id': market.id}, 
                        user=request.user)
            
            success_response = ApiResponse(
                success=True,
                code=201,
                data={
                    'location_id': location.id,
                    'market_id': market.id,
                    'city': location.city.name,
                    'next_step': 'contact'
                },
                message='Market location created successfully.',
            )
            
            return Response(success_response, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            log_error(e, context={'request_data': request.data}, user=request.user)
            return create_error_response(e, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(e, context={'request_data': request.data, 'view': 'MarketLocationCreateAPIView'}, user=request.user)
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketContactCreateAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MarketContactCreateSerializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):
            # بررسی مالکیت Market
            market_id = serializer.validated_data.get('market')
            try:
                market = Market.objects.get(id=market_id, user=request.user)
            except Market.DoesNotExist:
                return Response(
                    ApiResponse(
                        success=False,
                        code=404,
                        error={'code': 'market_not_found', 'detail': 'Market not found or access denied'}
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # ایجاد MarketContact
            contact = serializer.save()
            
            success_response = ApiResponse(
                success=True,
                code=201,
                data={
                    'contact_id': contact.id,
                    'market_id': market.id,
                    'mobile': contact.first_mobile_number,
                    'next_step': 'payment_gateway'
                },
                message='Market contact created successfully.',
            )
            
            return Response(success_response, status=status.HTTP_201_CREATED)


# اضافه شده: View برای انتخاب درگاه پرداخت
class PaymentGatewayAPIView(ErrorHandlerMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, market_id):
        try:
            log_info("Payment gateway selection request received", 
                    context={'user_id': request.user.id, 'market_id': market_id}, 
                    user=request.user)
            
            try:
                market = get_object_or_404(Market, id=market_id, user=request.user)
            except Market.DoesNotExist:
                log_security_event("Unauthorized market access for payment gateway", 
                                 user=request.user, 
                                 details={'market_id': market_id})
                return Response(
                    ApiResponse(
                        success=False,
                        code=404,
                        error={'code': 'market_not_found', 'detail': 'Market not found'}
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = PaymentGatewaySerializer(data=request.data)
            
            if not serializer.is_valid():
                log_warning("Payment gateway validation failed", 
                           context={'errors': serializer.errors}, 
                           user=request.user)
                return Response(handle_validation_errors(serializer.errors), 
                              status=status.HTTP_400_BAD_REQUEST)
            
            gateway_type = serializer.validated_data['gateway_type']
            gateway_key = serializer.validated_data.get('gateway_key')
            
            # ذخیره انتخاب درگاه with transaction
            with transaction.atomic():
                market.payment_gateway_type = gateway_type
                if gateway_key:
                    market.payment_gateway_key = gateway_key
                market.save()
                
                log_user_action(request.user, 'UPDATE', 'Market', market.id, 
                              {'gateway_type': gateway_type, 'has_gateway_key': bool(gateway_key)})
                
                log_info("Payment gateway selected successfully", 
                        context={'market_id': market.id, 'gateway_type': gateway_type}, 
                        user=request.user)
            
            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    'market_id': market.id,
                    'gateway_type': gateway_type,
                    'next_step': 'subscription_payment'
                },
                message='Payment gateway selected successfully.',
            )
            
            return Response(success_response, status=status.HTTP_200_OK)
            
        except PaymentError as e:
            log_error(e, context={'market_id': market_id, 'request_data': request.data}, user=request.user)
            return create_error_response(e, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            log_error(e, context={'market_id': market_id, 'view': 'PaymentGatewayAPIView'}, user=request.user)
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)


# اضافه شده: View برای محاسبه حق اشتراک
class SubscriptionFeeCalculatorAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = SubscriptionFeeCalculatorSerializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):
            sub_category_id = serializer.validated_data['sub_category_id']
            sub_category = SubCategory.objects.get(id=sub_category_id)
            
            # محاسبه حق اشتراک
            base_fee = sub_category.market_fee
            
            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    'sub_category': sub_category.title,
                    'base_fee': float(base_fee),
                    'currency': 'تومان',
                    'payment_required': True
                },
                message='Subscription fee calculated successfully.',
            )
            
            return Response(success_response, status=status.HTTP_200_OK)


# اضافه شده: View برای پرداخت حق اشتراک
class SubscriptionPaymentAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, market_id):
        try:
            market = get_object_or_404(Market, id=market_id, user=request.user)
        except Market.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error={'code': 'market_not_found', 'detail': 'Market not found'}
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SubscriptionPaymentSerializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):
            payment_method = serializer.validated_data['payment_method']
            discount_code = serializer.validated_data.get('discount_code')
            
            # محاسبه حق اشتراک
            base_fee = market.sub_category.market_fee
            discount_amount = 0
            
            if discount_code:
                discount = Discount.objects.get(code=discount_code)
                discount_amount = (base_fee * discount.percentage) / 100
            
            final_fee = base_fee - discount_amount
            
            # ذخیره اطلاعات پرداخت
            market.subscription_fee = final_fee
            market.subscription_payment_status = 'pending'
            market.save()
            
            if payment_method == 'wallet':
                # پرداخت از کیف پول
                return self.process_wallet_payment(market, final_fee)
            else:
                # پرداخت از درگاه
                return self.process_gateway_payment(market, final_fee)
    
    def process_wallet_payment(self, market, amount):
        # بررسی موجودی کیف پول
        wallet, _ = Wallet.objects.get_or_create(user=market.user)
        
        if wallet.balance >= amount:
            # پرداخت از کیف پول
            wallet.balance -= amount
            wallet.save()
            
            # به‌روزرسانی وضعیت
            market.subscription_payment_status = 'paid'
            market.subscription_payment_date = timezone.now()
            market.is_paid = True
            market.save()
            
            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    'payment_status': 'paid',
                    'payment_method': 'wallet',
                    'amount': float(amount),
                    'market_id': market.id
                },
                message='Subscription paid successfully from wallet.',
            )
            
            return Response(success_response, status=status.HTTP_200_OK)
        else:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error={'code': 'insufficient_balance', 'detail': 'Insufficient wallet balance'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def process_gateway_payment(self, market, amount):
        # ایجاد درخواست پرداخت
        payment = Payment.objects.create(
            user=market.user,
            amount=amount,
            description=f'پرداخت حق اشتراک {market.name}',
            status='pending'
        )
        
        # اتصال به درگاه پرداخت
        gateway_url = self.create_gateway_payment(payment, amount)
        
        success_response = ApiResponse(
            success=True,
            code=200,
            data={
                'payment_status': 'pending',
                'payment_method': 'gateway',
                'amount': float(amount),
                'payment_id': payment.id,
                'gateway_url': gateway_url
            },
            message='Redirect to payment gateway.',
        )
        
        return Response(success_response, status=status.HTTP_200_OK)
    
    def create_gateway_payment(self, payment, amount):
        # اتصال به درگاه پرداخت (Zarinpal, etc.)
        # این قسمت باید با درگاه پرداخت موجود ادغام شود
        return f'/payment/gateway/{payment.id}/'


# اضافه شده: View برای ایجاد فروشگاه یکپارچه
class IntegratedMarketCreateAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = IntegratedMarketCreateSerializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):
            # ایجاد Market
            market_data = {
                'template': serializer.validated_data['template'],
                'business_id': serializer.validated_data['business_id'],
                'name': serializer.validated_data['name'],
                'description': serializer.validated_data.get('description'),
                'national_code': serializer.validated_data.get('national_code'),
                'sub_category_id': serializer.validated_data['sub_category'],
                'slogan': serializer.validated_data.get('slogan'),
                'working_hours': serializer.validated_data.get('working_hours'),
            }
            
            market = Market.objects.create(
                user=request.user,
                **market_data
            )
            
            # ایجاد MarketLocation
            location_data = {
                'market': market,
                'country_id': serializer.validated_data['country'],
                'province_id': serializer.validated_data['province'],
                'city_id': serializer.validated_data['city'],
                'address': serializer.validated_data['address'],
                'zip_code': serializer.validated_data.get('zip_code'),
                'latitude': serializer.validated_data.get('latitude'),
                'longitude': serializer.validated_data.get('longitude'),
            }
            
            location = MarketLocation.objects.create(**location_data)
            
            # ایجاد MarketContact
            contact_data = {
                'market': market,
                'first_mobile_number': serializer.validated_data['first_mobile_number'],
                'second_mobile_number': serializer.validated_data.get('second_mobile_number'),
                'telephone': serializer.validated_data.get('telephone'),
                'fax': serializer.validated_data.get('fax'),
                'email': serializer.validated_data.get('email'),
                'website_url': serializer.validated_data.get('website_url'),
                'instagram_id': serializer.validated_data.get('instagram_id'),
                'telegram_id': serializer.validated_data.get('telegram_id'),
                'messenger_ids': serializer.validated_data.get('messenger_ids'),
            }
            
            contact = MarketContact.objects.create(**contact_data)
            
            success_response = ApiResponse(
                success=True,
                code=201,
                data={
                    'market_id': market.id,
                    'location_id': location.id,
                    'contact_id': contact.id,
                    'next_step': 'payment_gateway'
                },
                message='Integrated market created successfully.',
            )
            
            return Response(success_response, status=status.HTTP_201_CREATED)