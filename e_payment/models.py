from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator
import uuid

'''

    You must use customer and vendor in accounts app .
    this is just a vision, not complete project and every things.

'''

class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="User"
    )
    stripe_customer_id = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Stripe Customer ID"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"{self.user.email}"


class Vendor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="User"
    )
    business_name = models.CharField(max_length=255, verbose_name="Business Name")
    stripe_account_id = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Stripe Account ID"
    )
    is_verified = models.BooleanField(default=False, verbose_name="Is Verified")
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('5.00'),
        verbose_name="Commission Rate (%)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"

    def __str__(self):
        return self.business_name


class Product(models.Model):
    PRODUCT_TYPE_CHOICES = (
        ('physical', 'Physical Product'),
        ('digital', 'Digital Product'),
        ('service', 'Service'),
    )
    
    vendor = models.ForeignKey(
        Vendor, 
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Vendor"
    )
    name = models.CharField(max_length=255, verbose_name="Name")
    description = models.TextField(verbose_name="Description")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Price",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        max_length=3, 
        default='USD',
        verbose_name="Currency"
    )
    product_type = models.CharField(
        max_length=10, 
        choices=PRODUCT_TYPE_CHOICES,
        default='physical',
        verbose_name="Product Type"
    )
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock Quantity"
    )
    sku = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="SKU"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def is_in_stock(self):
        return self.stock_quantity > 0
    
    
class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )

    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Customer"
    )
    order_number = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="Order Number"
    )
    status = models.CharField(
        max_length=20, 
        choices=ORDER_STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Total Amount",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        max_length=3, 
        default='USD',
        verbose_name="Currency"
    )
    shipping_address = models.JSONField(
        default=dict,
        verbose_name="Shipping Address"
    )
    billing_address = models.JSONField(
        default=dict,
        verbose_name="Billing Address"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Order"
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT,
        verbose_name="Product"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantity",
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Unit Price",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Total Price",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('crypto', 'Cryptocurrency'),
        ('wallet', 'Wallet'),
    )

    order = models.OneToOneField(
        Order, 
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name="Order"
    )
    payment_id = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name="Payment ID"
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Amount",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        max_length=3, 
        default='USD',
        verbose_name="Currency"
    )
    status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name="Payment Method"
    )
    payment_gateway = models.CharField(
        max_length=50, 
        default='stripe',
        verbose_name="Payment Gateway"
    )
    transaction_id = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name="Transaction ID"
    )
    payment_date = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Payment Date"
    )
    refund_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Refund Amount",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    refund_reason = models.TextField(
        blank=True,
        verbose_name="Refund Reason"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payment_id} - {self.amount} {self.currency}"

    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = f"pay_{uuid.uuid4().hex[:16]}"
        
        # Set payment_date when status changes to completed
        if self.status == 'completed' and not self.payment_date:
            self.payment_date = timezone.now()
            
        super().save(*args, **kwargs)

    def is_refundable(self):
        return self.status == 'completed' and self.refund_amount < self.amount

    def get_available_refund_amount(self):
        return self.amount - self.refund_amount


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('charge', 'Charge'),
        ('refund', 'Refund'),
        ('payout', 'Payout'),
        ('transfer', 'Transfer'),
    )

    TRANSACTION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    payment = models.ForeignKey(
        Payment, 
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Payment"
    )
    transaction_type = models.CharField(
        max_length=20, 
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name="Transaction Type"
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Amount",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        max_length=3, 
        default='USD',
        verbose_name="Currency"
    )
    gateway_transaction_id = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name="Gateway Transaction ID"
    )
    status = models.CharField(
        max_length=20, 
        choices=TRANSACTION_STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    metadata = models.JSONField(
        default=dict,
        verbose_name="Metadata"
    )
    processed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Processed At"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency}"

    def save(self, *args, **kwargs):
        # Set processed_at when status changes to completed
        if self.status == 'completed' and not self.processed_at:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)


class Refund(models.Model):
    REFUND_STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )

    payment = models.ForeignKey(
        Payment, 
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name="Payment"
    )
    refund_id = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name="Refund ID"
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Amount",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        max_length=3, 
        default='USD',
        verbose_name="Currency"
    )
    status = models.CharField(
        max_length=20, 
        choices=REFUND_STATUS_CHOICES,
        default='requested',
        verbose_name="Status"
    )
    reason = models.TextField(verbose_name="Reason")
    customer_note = models.TextField(
        blank=True,
        verbose_name="Customer Note"
    )
    processed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Processed At"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Refund"
        verbose_name_plural = "Refunds"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.refund_id} - {self.amount} {self.currency}"

    def save(self, *args, **kwargs):
        if not self.refund_id:
            self.refund_id = f"ref_{uuid.uuid4().hex[:16]}"
            
        # Set processed_at when status changes to completed
        if self.status == 'completed' and not self.processed_at:
            self.processed_at = timezone.now()
            
        super().save(*args, **kwargs)


class Payout(models.Model):
    PAYOUT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    vendor = models.ForeignKey(
        Vendor, 
        on_delete=models.CASCADE,
        related_name='payouts',
        verbose_name="Vendor"
    )
    payout_id = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name="Payout ID"
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Amount",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        max_length=3, 
        default='USD',
        verbose_name="Currency"
    )
    status = models.CharField(
        max_length=20, 
        choices=PAYOUT_STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    payment_method = models.CharField(
        max_length=50, 
        verbose_name="Payment Method"
    )
    destination = models.CharField(
        max_length=255, 
        verbose_name="Destination"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    processed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Processed At"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Payout"
        verbose_name_plural = "Payouts"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payout_id} - {self.amount} {self.currency}"

    def save(self, *args, **kwargs):
        if not self.payout_id:
            self.payout_id = f"payout_{uuid.uuid4().hex[:16]}"
            
        # Set processed_at when status changes to completed
        if self.status == 'completed' and not self.processed_at:
            self.processed_at = timezone.now()
            
        super().save(*args, **kwargs)