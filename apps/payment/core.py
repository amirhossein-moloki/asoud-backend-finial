import requests, os
from uuid import UUID
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from apps.payment.models import Payment, Zarinpal
from apps.advertise.models import Advertisement
from apps.wallet.models import Wallet
from apps.wallet.core import WalletCore
from apps.cart.models import Order
from apps.market.models import Market

class PaymentCore:
    def pay(self, user, data):
        
        model = None
        match data.get('target'):
            
            case "advertisement":
                model = Advertisement
            case "wallet":
                model = Wallet
            case "order":
                model = Order
            case "market":
                model = Market

            case _:
                return False, "Incorrect taget Value"

        try:
            # Check if target is market and has personal gateway configured
            if data.get('target') == "market":
                market = Market.objects.get(id=data['target_id'])
                if market.payment_gateway_type == Market.PERSONAL_GATEWAY:
                    return self._process_personal_gateway_payment(user, market, data)

            target_content_type = ContentType.objects.get_for_model(model)
            gateway_content_type = ContentType.objects.get_for_model(Zarinpal)

            payment = Payment.objects.create(
                user = user,
                amount = data['amount'],
                target_content_type = target_content_type,
                target_id = UUID(data['target_id']),
                gateway_content_type = gateway_content_type,
                status = Payment.PENDING
            )

            zarinpal = Zarinpal.objects.create(
                payment=payment,  
                authority=''
            )

            payment.gateway_id = zarinpal.id
            payment.save()

        except:
            return False, 'Payment Creation Failed'

        callback_url = os.environ.get("PAYMENT_CALLBACK_URL") or getattr(settings, 'PAYMENT_CALLBACK_URL', None)
        if not callback_url:
            # Secure default; must be HTTPS in production
            callback_url = "https://asoud.ir/api/v1/user/payments/verify/"

        data = {
            'merchant_id': os.environ.get("ZARINPAL_MERCHANT_ID"),
            'amount': int(payment.amount),
            'currency': 'IRT',
            'description': 'Asoud payment',
            'callback_url': callback_url,
            'meta_data': {'payment': str(payment.id)}
        }

        url = f'https://{settings.ZARINPAL_URL}.zarinpal.com/pg/v4/payment/request.json'
        response = requests.post(url=url, json=data)

        jsonRes = response.json()
        try:
            authority = jsonRes['data']['authority']
        except Exception:
            return False, 'an error occured during connecting to zarinpal'
        
        # update zarinpal instance
        zarinpal.payment=payment
        zarinpal.authority=authority
        zarinpal.save()

        return True, zarinpal
    
    def verify(self, request):
        try:
            authority = request.GET.get('Authority')
            stat = request.GET.get('Status')
        except Exception:
            return False, 'no data is provided'
        
        if stat == "NOK":
            return False, 'status not OK'

        try:
            zarin = Zarinpal.objects.select_related('payment', 'payment__user').get(authority=authority)
        except Exception:
            return False, 'no payment found'

        if zarin.transaction_id:
            return False, 'already validated'
        
        if zarin.payment.status != Payment.PENDING:
            return False, 'Payment already processed'
        
        data = {
            'merchant_id': os.environ.get("ZARINPAL_MERCHANT_ID"),
            'amount': int(zarin.payment.amount),
            'authority': authority,
        }

        url = f'https://{settings.ZARINPAL_URL}.zarinpal.com/pg/v4/payment/verify.json'
        response = requests.post(url=url, json=data)
        jsonRes = response.json()

        with transaction.atomic():
            try:
                code = jsonRes['data']['code']
                ref_id = jsonRes['data']['ref_id']
            except:
                zarin.payment.status = Payment.FAILED
                zarin.payment.save()
                return False, "Verification Failed From Gateway"
            
            if code != 100:
                zarin.payment.status = Payment.FAILED
                zarin.payment.save()
                return False, "Verification Failed"
            
            # Idempotency: if a transaction_id already exists, avoid re-processing
            if zarin.transaction_id:
                return False, 'already validated'
            
            # Verify amount and integrity before post-processing
            verified_amount = int(jsonRes['data'].get('amount', 0)) if isinstance(jsonRes.get('data'), dict) else 0
            if verified_amount and int(zarin.payment.amount) != verified_amount:
                zarin.payment.status = Payment.FAILED
                zarin.payment.save()
                return False, 'Amount mismatch'
                
            # go for post payment processes
            post_payment = PostPaymentCore(zarin.payment.user)
            try:
                post_payment.payment_process(zarin.payment)
            except Exception as e:
                return False, str(e)
            
            # save ref_id to transaction_id
            zarin.transaction_id = ref_id
            zarin.verification_data = jsonRes
            zarin.save()

            zarin.payment.status = Payment.COMPLETE
            zarin.payment.save()

        return True, "Payment Successfull"
    
    def _process_personal_gateway_payment(self, user, market, data):
        """
        Process payment using personal gateway configuration.
        This method handles payments for markets that have selected personal gateway option.
        """
        try:
            gateway_config = market.personal_gateway_config
            if not gateway_config:
                return False, "Personal gateway configuration not found"
            
            # Create payment record for personal gateway
            target_content_type = ContentType.objects.get_for_model(Market)
            
            payment = Payment.objects.create(
                user=user,
                amount=data['amount'],
                target_content_type=target_content_type,
                target_id=UUID(data['target_id']),
                gateway_content_type=None,  # No specific gateway model for personal
                status=Payment.PENDING
            )
            
            # For personal gateway, we create a simple record without external API calls
            # The actual payment processing would be handled by the merchant's own system
            payment_info = {
                'payment_id': str(payment.id),
                'amount': data['amount'],
                'gateway_type': 'personal',
                'gateway_name': gateway_config.get('gateway_name', 'Personal Gateway'),
                'merchant_id': gateway_config.get('merchant_id'),
                'redirect_url': f"/payment/personal/{payment.id}/",
                'message': 'Payment created successfully. Please complete payment through your personal gateway.'
            }
            
            return True, payment_info
            
        except Exception as e:
            return False, f"Personal gateway payment creation failed: {str(e)}"
    

class PostPaymentCore:
    def __init__(self, user):
        self.user = user

    def payment_process(self, payment: Payment):
        target_model = payment.target_content_type.model_class()

        if target_model == Advertisement:
            self.update_advertisement(
                payment.target_id
            )
        
        elif target_model == Wallet:
            self.create_wallet_transaction(
                payment.target_id,
                payment.amount
            )

        elif target_model == Market:
            self.update_market(
                payment.target_id
            )

        else :
                self.complete_order(
                    payment.target_id
                )    

    def wallet_process(self, target:str, pk:str, amount:float = None, wallet_id:str = None):
        if target == 'advertisement':
            self.update_advertisement(
                pk
            )
            WalletCore.decrease_balance(
                self.user, 
                wallet_id,
                amount
            )

        elif target == 'wallet':
            WalletCore.transaction(
                self.user, 
                wallet_id,
                pk,
                amount
            )
        
        else :
            self.complete_order(
                pk
            )
            WalletCore.decrease_balance(
                self.user, 
                wallet_id,
                amount
            )


    def update_advertisement(self, pk:str):
        ad = Advertisement.objects.get(id=pk)
        
        ad.is_paid = True
        ad.save()

    def create_wallet_transaction(self, pk:str, amount: float):
        success, data = WalletCore.increase_balance(self.user, pk, amount)
        if not success:
            raise Exception(data)

    def update_market(self, target_id):
        obj = Market.objects.get(id=target_id)
        obj.status = 'queue'
        obj.is_paid = True
        obj.save()

    def complete_order(self, pk:str):
        order = Order.objects.get(id=pk)
        order.status = Order.COMPLETED
        order.is_paid = True
        order.save()

