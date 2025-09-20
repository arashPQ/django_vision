from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator

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