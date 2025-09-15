from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

'''
    If you are using PostgreSQL you can use JSONfield better.

    The algorithm and logic of adding items to the View is up to you.
'''


class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name='brand name')
    country = models.CharField(max_length=50, verbose_name='country')
    established_year = models.IntegerField(verbose_name='established year')
    logo = models.ImageField(upload_to='brands/logos/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'brand name'
        verbose_name_plural = 'brands name'
    
    def __str__(self):
        return self.name

class Category(models.Model):
    CATEGORY_TYPES = [
        ('mobile', 'mobile'),
        ('laptop', 'laptop'),
        ('desktop', 'desktop'),
        ('console', 'console'),
        ('accessory', 'accessory'),
        ('audio', 'audio'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='category name')
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, verbose_name='category type')
    description = models.TextField(verbose_name='description', blank=True)
    
    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return f"{self.name} - {self.get_category_type_display()}"

class Product(models.Model):
    CONDITION_CHOICES = [
        ('new', 'new'),
        ('used', 'used'),
        ('refurbished', 'refurbished'),
    ]
    
    # Base info
    name = models.CharField(max_length=200, verbose_name='product name')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name='brand')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='category')
    model = models.CharField(max_length=100, verbose_name='model', blank=True)
    release_year = models.IntegerField(verbose_name='release year', validators=[MinValueValidator(1990), MaxValueValidator(2030)])
    
    # Technical info
    description = models.TextField(verbose_name='description')
    specifications = models.JSONField(verbose_name='technical specifications', default=dict)
    
    # Price 
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='price')
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='discount price', null=True, blank=True)
    stock = models.IntegerField(verbose_name='stock', default=0)
    sku = models.CharField(max_length=50, unique=True, verbose_name='product sku')
    
    # condition
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, verbose_name='condition')
    is_active = models.BooleanField(default=True, verbose_name='active')
    is_featured = models.BooleanField(default=False, verbose_name='featured')
    
    # date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'product'
        verbose_name_plural = 'products'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.brand.name} {self.name}"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/images/')
    alt_text = models.CharField(max_length=100, verbose_name='alt text', blank=True)
    is_main = models.BooleanField(default=False, verbose_name='main')
    
    class Meta:
        verbose_name = 'product image'
        verbose_name_plural = 'product images'
    
    def __str__(self):
        return f"Image for {self.product.name}"


class MobileSpecification(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='mobile_specs')
    screen_size = models.DecimalField(max_digits=4, decimal_places=2, verbose_name='screen size (inch)')
    resolution = models.CharField(max_length=50, verbose_name='resolution')
    ram = models.IntegerField(verbose_name='RAM (GB)')
    storage = models.IntegerField(verbose_name='storage (GB)')
    battery = models.IntegerField(verbose_name='battery (mAh)')
    camera_main = models.CharField(max_length=100, verbose_name='main camera')
    camera_front = models.CharField(max_length=100, verbose_name='front camera')
    os = models.CharField(max_length=50, verbose_name='OS')
    cpu = models.CharField(max_length=100, verbose_name='CPU')
    gpu = models.CharField(max_length=100, verbose_name='GPU', blank=True)
    sim_count = models.IntegerField(verbose_name='sim count', default=1)
    weight = models.DecimalField(max_digits=5, decimal_places=1, verbose_name='weight (g)')
    
    class Meta:
        verbose_name = 'mobile specification'
        verbose_name_plural = 'mobiles specification'

class LaptopSpecification(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='laptop_specs')
    screen_size = models.DecimalField(max_digits=3, decimal_places=1, verbose_name='screen size (inch)')
    resolution = models.CharField(max_length=50, verbose_name='resolution')
    ram = models.IntegerField(verbose_name='RAM (GB)')
    storage = models.IntegerField(verbose_name='storage (GB)')
    storage_type = models.CharField(max_length=20, choices=[('hdd', 'HDD'), ('ssd', 'SSD'), ('nvme', 'NVMe')], verbose_name='storage type')
    cpu = models.CharField(max_length=100, verbose_name='cpu')
    gpu = models.CharField(max_length=100, verbose_name='gpu')
    os = models.CharField(max_length=50, verbose_name='OS')
    battery_life = models.DecimalField(max_digits=4, decimal_places=1, verbose_name='battery life')
    weight = models.DecimalField(max_digits=4, decimal_places=1, verbose_name='weight (kg)')
    ports = models.TextField(verbose_name='ports', blank=True)
    
    class Meta:
        verbose_name = 'laptop specification'
        verbose_name_plural = 'laptops specification'

class ConsoleSpecification(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='console_specs')
    storage = models.IntegerField(verbose_name='storage (GB)')
    cpu = models.CharField(max_length=100, verbose_name='cpu')
    gpu = models.CharField(max_length=100, verbose_name='gpu')
    ram = models.IntegerField(verbose_name='RAM (GB)')
    max_resolution = models.CharField(max_length=50, verbose_name='max resolution')
    controller_included = models.BooleanField(default=True, verbose_name='controller included')
    vr_support = models.BooleanField(default=False, verbose_name='vr support')
    online_features = models.TextField(verbose_name='online_features', blank=True)
    
    class Meta:
        verbose_name = 'console specification'
        verbose_name_plural = 'consoles specification'