from apps.wallet.models import Wallet, Transaction
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from apps.users.models import User
import logging

logger = logging.getLogger(__name__)


class WalletCore:

    @staticmethod
    def increase_balance(user:User, pk:str, amount:float):
        if amount <= 0:
            return False, "Invalid amount"
        
        try:
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(id=pk)
                wallet.balance = F('balance') + amount
                wallet.save()
                wallet.refresh_from_db(fields=['balance'])
                
                logger.info('Wallet increased successfully')
                Transaction.objects.create(
                    user = user,
                    from_wallet = wallet,
                    to_wallet = wallet,
                    action = 'charge', 
                    amount = amount
                )
        except Exception as e:
            return False, str(e)

        return True, wallet.balance
    
    @staticmethod
    def decrease_balance(user:User, pk:str, amount:float):
        if amount <= 0:
            return False, "Invalid amount"
        
        try:
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(id=pk)
                if wallet.balance < amount:
                    return False, "Insufficient Balance"
                wallet.balance = F('balance') - amount
                wallet.save()
                wallet.refresh_from_db(fields=['balance'])
                
                Transaction.objects.create(
                    user = user,
                    from_wallet = wallet,
                    to_wallet = wallet,
                    action = 'spend', 
                    amount = amount
                )
        except Exception as e:
            return False, str(e)
        
        return True, wallet.balance
    
    @staticmethod
    def transaction(user:User, from_pk:str, to_pk:str, amount: float):
        if amount <= 0:
            return False, "Invalid amount"
        
        try:
            # Always lock in a consistent order to avoid deadlocks
            first_id, second_id = sorted([from_pk, to_pk])
            with transaction.atomic():
                first_wallet = Wallet.objects.select_for_update().get(id=first_id)
                second_wallet = Wallet.objects.select_for_update().get(id=second_id)
                from_wallet = first_wallet if first_wallet.id == from_pk else second_wallet
                to_wallet = second_wallet if first_wallet.id == from_pk else first_wallet

                if from_wallet.balance < amount:
                    return False, "Insufficient Balance"

                from_wallet.balance = F('balance') - amount
                to_wallet.balance = F('balance') + amount

                from_wallet.save()
                to_wallet.save()

                from_wallet.refresh_from_db(fields=['balance'])
                to_wallet.refresh_from_db(fields=['balance'])

                Transaction.objects.create(
                    user = user,
                    from_wallet = from_wallet,
                    to_wallet = to_wallet,
                    action = 'exchange', 
                    amount = amount
                )
        except Exception as e:
            return False, str(e)
        
        return True, (from_wallet.balance, to_wallet.balance)

