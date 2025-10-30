"""
Inventory Management Models for ASOUD Platform
"""

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from apps.base.models import BaseModel
from apps.users.models import User
from apps.product.models import Product
from apps.cart.models import Order

class InventoryLog(BaseModel):
    """
    Log of all inventory movements
    """
    
    RESERVE = 'reserve'
    RELEASE = 'release'
    CONFIRM = 'confirm'
    ADD = 'add'
    SUBTRACT = 'subtract'
    ADJUSTMENT = 'adjustment'
    
    ACTION_CHOICES = [
        (RESERVE, 'Reserve'),
        (RELEASE, 'Release'),
        (CONFIRM, 'Confirm'),
        (ADD, 'Add'),
        (SUBTRACT, 'Subtract'),
        (ADJUSTMENT, 'Adjustment'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_logs',
        verbose_name='Product'
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='Action'
    )
    
    quantity = models.PositiveIntegerField(
        verbose_name='Quantity'
    )
    
    remaining_stock = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Remaining Stock'
    )
    
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_logs',
        verbose_name='Order'
    )
    
    reason = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Reason'
    )
    
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Notes'
    )
    
    class Meta:
        db_table = 'inventory_log'
        ordering = ['-created_at']
        verbose_name = 'Inventory Log'
        verbose_name_plural = 'Inventory Logs'
    
    def __str__(self):
        return f"{self.product.name} - {self.action} - {self.quantity}"

class StockAlert(BaseModel):
    """
    Stock alert configuration and history
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_alerts',
        verbose_name='Product'
    )
    
    threshold = models.PositiveIntegerField(
        default=10,
        verbose_name='Low Stock Threshold'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )
    
    last_alert_sent = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last Alert Sent'
    )
    
    alert_frequency = models.PositiveIntegerField(
        default=24,
        help_text='Hours between alerts',
        verbose_name='Alert Frequency'
    )
    
    class Meta:
        db_table = 'stock_alert'
        verbose_name = 'Stock Alert'
        verbose_name_plural = 'Stock Alerts'
        unique_together = ['product', 'threshold']
    
    def __str__(self):
        return f"{self.product.name} - Alert at {self.threshold}"

class InventoryAdjustment(BaseModel):
    """
    Inventory adjustments and corrections
    """
    
    ADJUSTMENT = 'adjustment'
    CORRECTION = 'correction'
    DAMAGE = 'damage'
    THEFT = 'theft'
    RETURN = 'return'
    
    TYPE_CHOICES = [
        (ADJUSTMENT, 'Adjustment'),
        (CORRECTION, 'Correction'),
        (DAMAGE, 'Damage'),
        (THEFT, 'Theft'),
        (RETURN, 'Return'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_adjustments',
        verbose_name='Product'
    )
    
    adjustment_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='Adjustment Type'
    )
    
    quantity_change = models.IntegerField(
        verbose_name='Quantity Change',
        help_text='Positive for increase, negative for decrease'
    )
    
    previous_stock = models.PositiveIntegerField(
        verbose_name='Previous Stock'
    )
    
    new_stock = models.PositiveIntegerField(
        verbose_name='New Stock'
    )
    
    reason = models.CharField(
        max_length=255,
        verbose_name='Reason'
    )
    
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Notes'
    )
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_adjustments',
        verbose_name='Approved By'
    )
    
    is_approved = models.BooleanField(
        default=False,
        verbose_name='Is Approved'
    )
    
    class Meta:
        db_table = 'inventory_adjustment'
        ordering = ['-created_at']
        verbose_name = 'Inventory Adjustment'
        verbose_name_plural = 'Inventory Adjustments'
    
    def __str__(self):
        return f"{self.product.name} - {self.adjustment_type} - {self.quantity_change}"

class InventoryReport(BaseModel):
    """
    Generated inventory reports
    """
    
    SUMMARY = 'summary'
    LOW_STOCK = 'low_stock'
    TURNOVER = 'turnover'
    MOVEMENTS = 'movements'
    
    REPORT_TYPE_CHOICES = [
        (SUMMARY, 'Summary'),
        (LOW_STOCK, 'Low Stock'),
        (TURNOVER, 'Turnover'),
        (MOVEMENTS, 'Movements'),
    ]
    
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        verbose_name='Report Type'
    )
    
    market = models.ForeignKey(
        'market.Market',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='inventory_reports',
        verbose_name='Market'
    )
    
    period_start = models.DateTimeField(
        verbose_name='Period Start'
    )
    
    period_end = models.DateTimeField(
        verbose_name='Period End'
    )
    
    data = models.JSONField(
        verbose_name='Report Data'
    )
    
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports',
        verbose_name='Generated By'
    )
    
    is_archived = models.BooleanField(
        default=False,
        verbose_name='Is Archived'
    )
    
    class Meta:
        db_table = 'inventory_report'
        ordering = ['-created_at']
        verbose_name = 'Inventory Report'
        verbose_name_plural = 'Inventory Reports'
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.period_start} to {self.period_end}"

class InventorySettings(BaseModel):
    """
    Inventory management settings
    """
    
    market = models.OneToOneField(
        'market.Market',
        on_delete=models.CASCADE,
        related_name='inventory_settings',
        verbose_name='Market'
    )
    
    auto_reserve_stock = models.BooleanField(
        default=True,
        verbose_name='Auto Reserve Stock'
    )
    
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        verbose_name='Low Stock Threshold'
    )
    
    alert_frequency = models.PositiveIntegerField(
        default=24,
        help_text='Hours between low stock alerts',
        verbose_name='Alert Frequency'
    )
    
    auto_reorder = models.BooleanField(
        default=False,
        verbose_name='Auto Reorder'
    )
    
    reorder_point = models.PositiveIntegerField(
        default=20,
        verbose_name='Reorder Point'
    )
    
    reorder_quantity = models.PositiveIntegerField(
        default=50,
        verbose_name='Reorder Quantity'
    )
    
    track_movements = models.BooleanField(
        default=True,
        verbose_name='Track Movements'
    )
    
    movement_retention_days = models.PositiveIntegerField(
        default=365,
        verbose_name='Movement Retention Days'
    )
    
    class Meta:
        db_table = 'inventory_settings'
        verbose_name = 'Inventory Settings'
        verbose_name_plural = 'Inventory Settings'
    
    def __str__(self):
        return f"Inventory Settings - {self.market.name}"

class InventoryMetrics(BaseModel):
    """
    Inventory performance metrics
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_metrics',
        verbose_name='Product'
    )
    
    date = models.DateField(
        verbose_name='Date'
    )
    
    opening_stock = models.PositiveIntegerField(
        verbose_name='Opening Stock'
    )
    
    closing_stock = models.PositiveIntegerField(
        verbose_name='Closing Stock'
    )
    
    units_sold = models.PositiveIntegerField(
        default=0,
        verbose_name='Units Sold'
    )
    
    units_received = models.PositiveIntegerField(
        default=0,
        verbose_name='Units Received'
    )
    
    units_adjusted = models.IntegerField(
        default=0,
        verbose_name='Units Adjusted'
    )
    
    turnover_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Turnover Rate'
    )
    
    days_in_stock = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Days in Stock'
    )
    
    class Meta:
        db_table = 'inventory_metrics'
        ordering = ['-date']
        verbose_name = 'Inventory Metrics'
        verbose_name_plural = 'Inventory Metrics'
        unique_together = ['product', 'date']
    
    def __str__(self):
        return f"{self.product.name} - {self.date}"

class InventoryAudit(BaseModel):
    """
    Inventory audit trail
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_audits',
        verbose_name='Product'
    )
    
    action = models.CharField(
        max_length=50,
        verbose_name='Action'
    )
    
    old_value = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Old Value'
    )
    
    new_value = models.JSONField(
        null=True,
        blank=True,
        verbose_name='New Value'
    )
    
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_audits',
        verbose_name='Changed By'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Address'
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name='User Agent'
    )
    
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Notes'
    )
    
    class Meta:
        db_table = 'inventory_audit'
        ordering = ['-created_at']
        verbose_name = 'Inventory Audit'
        verbose_name_plural = 'Inventory Audits'
    
    def __str__(self):
        return f"{self.product.name} - {self.action} - {self.created_at}"




