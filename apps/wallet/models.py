from apps.base.models  import models, BaseModel
from django.utils.translation import gettext_lazy as _
from apps.users.models import User
# Create your models here.

class Wallet(BaseModel):
    user = models.OneToOneField(
        User,
        related_name='wallet',
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )

    balance = models.FloatField(
        default=0,
        verbose_name=_('Balance')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Wallet')
        verbose_name_plural = _('Wallets')
    
class Transaction(BaseModel):
    user = models.ForeignKey(
        User,
        related_name='wallet_transactions',
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    from_wallet = models.ForeignKey(
        Wallet, 
        on_delete=models.CASCADE, 
        related_name='sent_transactions',
        verbose_name=_('From Wallet')
    )
    to_wallet = models.ForeignKey(
        Wallet, 
        on_delete=models.CASCADE, 
        related_name='received_transactions', 
        null=True, 
        blank=True,
        verbose_name=_('To Wallet')
    )
    action = models.CharField(
        max_length=100,
        verbose_name=_('Action')
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=3,
        verbose_name=_('Amount')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Wallet Transaction')
        verbose_name_plural = _('Wallet Transactions')