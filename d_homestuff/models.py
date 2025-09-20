from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from django.core.exceptions import ValidationError
from decimal import Decimal
import datetime

class Category(MPTTModel):
    name = models.CharField(max_length=100, verbose_name="Name")
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                           verbose_name="Parent Category", related_name="children")
    description = models.TextField(verbose_name="Description", blank=True)
    image = models.ImageField(upload_to='categories/', verbose_name="Image", blank=True, 
                             validators=[MaxValueValidator(5 * 1024 * 1024)])  # Max 5MB
    slug = models.SlugField(unique=True, verbose_name="Slug", allow_unicode=True)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    class MPTTMeta:
        order_insertion_by = ['name']
        verbose_name = "Category"
        verbose_name_plural = "Categories"
    
    class Meta:
        ordering = ['tree_id', 'lft']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def clean(self):
        if self.parent and self.parent == self:
            raise ValidationError("A category cannot be its own parent.")
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name="Name")
    description = models.TextField(verbose_name="Description", blank=True)
    logo = models.ImageField(upload_to='brands/', verbose_name="Logo", blank=True,
                            validators=[MaxValueValidator(2 * 1024 * 1024)])  # Max 2MB
    slug = models.SlugField(unique=True, verbose_name="Slug", allow_unicode=True)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class ProductAttribute(models.Model):
    name = models.CharField(max_length=100, verbose_name="Name")
    description = models.TextField(verbose_name="Description", blank=True)
    
    class Meta:
        verbose_name = "Product Attribute"
        verbose_name_plural = "Product Attributes"
    
    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, 
                                 verbose_name="Attribute", related_name="values")
    value = models.CharField(max_length=100, verbose_name="Value")
    
    class Meta:
        verbose_name = "Attribute Value"
        verbose_name_plural = "Attribute Values"
        unique_together = ('attribute', 'value')
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class Product(models.Model):
    PRODUCT_TYPE_CHOICES = (
        ('physical', 'Physical Product'),
        ('digital', 'Digital Product'),         #   like course, catalogs, pdf books ...
    )
    
    name = models.CharField(max_length=200, verbose_name="Name")
    slug = models.SlugField(unique=True, verbose_name="Slug", allow_unicode=True)
    description = models.TextField(verbose_name="Description")
    short_description = models.TextField(verbose_name="Short Description", max_length=500)
    category = TreeForeignKey(Category, on_delete=models.CASCADE, 
                             verbose_name="Category", related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name="Brand", related_name="products")
    attributes = models.ManyToManyField(ProductAttributeValue, through='ProductAttributeValueThrough',
                                       verbose_name="Attributes", blank=True)
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        verbose_name="Base Price",
        validators=[MinValueValidator(Decimal('0.01'))]  # Price must be greater than zero
    )
    discount_percent = models.PositiveIntegerField(
        default=0, 
        validators=[MaxValueValidator(100)],  # Discount cannot exceed 100%
        verbose_name="Discount Percentage"
    )
    final_price = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        verbose_name="Final Price", 
        editable=False
    )
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    is_featured = models.BooleanField(default=False, verbose_name="Featured")
    product_type = models.CharField(
        max_length=10, 
        choices=PRODUCT_TYPE_CHOICES, 
        default='physical', 
        verbose_name="Product Type"
    )
    stock_quantity = models.PositiveIntegerField(
        default=0, 
        verbose_name="Stock Quantity",
        validators=[MinValueValidator(0)]  # Stock cannot be negative
    )
    weight = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name="Weight (kg)", 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]  # Weight must be greater than zero
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        
        # Calculate final price
        discount_amount = (self.base_price * Decimal(self.discount_percent)) / Decimal(100)
        self.final_price = self.base_price - discount_amount
        
        super().save(*args, **kwargs)
    
    def clean(self):
        # Base price must be greater than zero
        if self.base_price <= 0:
            raise ValidationError("Base price must be greater than zero.")
        
        # Stock quantity cannot be negative
        if self.stock_quantity < 0:
            raise ValidationError("Stock quantity cannot be negative.")
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})
    
    def is_in_stock(self):
        return self.stock_quantity > 0
    
    def get_discount_amount(self):
        return self.base_price - self.final_price


class ProductAttributeValueThrough(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    attribute_value = models.ForeignKey(ProductAttributeValue, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('product', 'attribute_value')
    
    def __str__(self):
        return f"{self.product.name} - {self.attribute_value}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, 
                               verbose_name="Product", related_name="images")
    image = models.ImageField(
        upload_to='products/', 
        verbose_name="Image",
        validators=[MaxValueValidator(5 * 1024 * 1024)]  # Max 5MB
    )
    alt_text = models.CharField(max_length=100, verbose_name="Alt Text", blank=True)
    is_default = models.BooleanField(default=False, verbose_name="Default Image")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ['-is_default', 'created_at']
    
    def save(self, *args, **kwargs):
        # If this image is marked as default, deactivate other default images for this product
        if self.is_default:
            ProductImage.objects.filter(product=self.product, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} - Image {self.id}"


#       You can use accounts app for this model

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="User")
    phone_number = models.CharField(max_length=15, verbose_name="Phone Number")
    national_code = models.CharField(
        max_length=10, 
        verbose_name="National Code", 
        blank=True,
        validators=[MinValueValidator(1000000000), MaxValueValidator(9999999999)]  # Must be 10 digits
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name="Birth Date")
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, verbose_name="Gender")
    credit = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0, 
        verbose_name="Credit",
        validators=[MinValueValidator(0)]  # Credit cannot be negative
    )
    
    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
    
    def clean(self):
        # Validate national code format (simple validation)
        if self.national_code and len(self.national_code) != 10:
            raise ValidationError("National code must be 10 digits.")
        
        # Birth date cannot be in the future
        if self.birth_date and self.birth_date > datetime.date.today():
            raise ValidationError("Birth date cannot be in the future.")
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.phone_number}"


class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, 
                                verbose_name="Customer", related_name="addresses")
    title = models.CharField(max_length=100, verbose_name="Title")
    recipient_name = models.CharField(max_length=100, verbose_name="Recipient Name")
    phone_number = models.CharField(max_length=15, verbose_name="Phone Number")
    province = models.CharField(max_length=50, verbose_name="Province")
    city = models.CharField(max_length=50, verbose_name="City")
    postal_address = models.TextField(verbose_name="Postal Address")
    postal_code = models.CharField(
        max_length=10, 
        verbose_name="Postal Code",
        validators=[MinValueValidator(1000000000), MaxValueValidator(9999999999)]  # Must be 10 digits
    )
    is_default = models.BooleanField(default=False, verbose_name="Default Address")
    
    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
    
    def save(self, *args, **kwargs):
        # If this address is marked as default, deactivate other default addresses for this user
        if self.is_default:
            Address.objects.filter(customer=self.customer, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    def clean(self):
        # Validate postal code format
        if self.postal_code and len(self.postal_code) != 10:
            raise ValidationError("Postal code must be 10 digits.")
    
    def __str__(self):
        return f"{self.customer} - {self.title}"


class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending Payment'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
    )
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, 
                                verbose_name="Customer", related_name="orders")
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Order Number")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Order Date")
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, 
                             default='pending', verbose_name="Order Status")
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, 
                                     default='pending', verbose_name="Payment Status")
    total_price = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0, 
        verbose_name="Total Price",
        validators=[MinValueValidator(0)]  # Price cannot be negative
    )
    discount_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0, 
        verbose_name="Discount Amount",
        validators=[MinValueValidator(0)]  # Discount cannot be negative
    )
    final_price = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0, 
        verbose_name="Final Price",
        validators=[MinValueValidator(0)]  # Final price cannot be negative
    )
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, 
                                        verbose_name="Shipping Address", related_name="shipping_orders")
    tracking_number = models.CharField(max_length=50, blank=True, verbose_name="Tracking Number")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-order_date']
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            self.order_number = f"ORD-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        super().save(*args, **kwargs)
    
    def clean(self):
        # Final price cannot be negative
        if self.final_price < 0:
            raise ValidationError("Final price cannot be negative.")
        
        # Discount cannot be greater than total price
        if self.discount_amount > self.total_price:
            raise ValidationError("Discount amount cannot be greater than total order amount.")
    
    def __str__(self):
        return f"{self.order_number} - {self.customer}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, 
                             verbose_name="Order", related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, 
                               verbose_name="Product", related_name="order_items")
    quantity = models.PositiveIntegerField(
        default=1, 
        verbose_name="Quantity",
        validators=[MinValueValidator(1)]  # Quantity must be at least 1
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        verbose_name="Unit Price",
        validators=[MinValueValidator(0)]  # Unit price cannot be negative
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        verbose_name="Total Price",
        validators=[MinValueValidator(0)]  # Total price cannot be negative
    )
    
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
    
    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    def clean(self):
        # Check if product has sufficient stock
        if self.quantity > self.product.stock_quantity:
            raise ValidationError(f"Insufficient stock for {self.product.name}. Available: {self.product.stock_quantity}")
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product.name}"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('online', 'Online Payment'),
        ('cash', 'Cash on Delivery'),
        ('bank', 'Bank Transfer'),
    )
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, 
                                verbose_name="Order", related_name="payment")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, 
                                     verbose_name="Payment Method")
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        verbose_name="Amount",
        validators=[MinValueValidator(0)]  # Amount cannot be negative
    )
    is_successful = models.BooleanField(default=False, verbose_name="Successful")
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Payment Date")
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name="Transaction ID")
    bank_name = models.CharField(max_length=50, blank=True, verbose_name="Bank Name")
    
    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-payment_date']
    
    def clean(self):
        # Payment amount must match order final price
        if self.amount != self.order.final_price:
            raise ValidationError("Payment amount must match the order final price.")
    
    def __str__(self):
        return f"{self.order.order_number} - {self.amount}"


class Review(models.Model):
    RATING_CHOICES = (
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, 
                               verbose_name="Product", related_name="reviews")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, 
                                verbose_name="Customer", related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES, 
        verbose_name="Rating",
        validators=[MinValueValidator(1), MaxValueValidator(5)]  # Rating must be between 1-5
    )
    title = models.CharField(max_length=200, verbose_name="Title")
    comment = models.TextField(verbose_name="Comment")
    is_approved = models.BooleanField(default=False, verbose_name="Approved")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        unique_together = ('product', 'customer')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.customer} - {self.rating} Stars"


class Wishlist(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, 
                                   verbose_name="Customer", related_name="wishlist")
    products = models.ManyToManyField(Product, verbose_name="Products", related_name="wishlists")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"
    
    def __str__(self):
        return f"{self.customer} - Wishlist"