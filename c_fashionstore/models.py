from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class ClothingBrand(models.Model):
    name = models.CharField(max_length=100, verbose_name='name of brand')
    country = models.CharField(max_length=50, verbose_name='brand country')
    style = models.CharField(max_length=100, verbose_name='style', blank=True)
    description = models.TextField(verbose_name='description', blank=True)
    logo = models.ImageField(upload_to='clothing_brands/logos/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'name of brand'
        verbose_name_plural = 'name of brands'
    
    def __str__(self):
        return self.name

class ClothingCategory(models.Model):
    CATEGORY_TYPES = [
        ('men', 'men'),
        ('women', 'women'),
        ('kids', 'kids'),
        ('unisex', 'unisex'),
    ]
    
    GARMENT_TYPES = [
        ('shirt', 'shirt'),
        ('pants', 'pants'),
        ('jacket', 'jacket'),
        ('dress', 'dress'),
        ('underwear', 'underwear'),
        ('shoes', 'shoes'),
        ('accessory', 'accessory'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='category name')
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, verbose_name='category type')
    garment_type = models.CharField(max_length=20, choices=GARMENT_TYPES, verbose_name='garment type')
    description = models.TextField(verbose_name='description', blank=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return f"{self.get_category_type_display()} - {self.get_garment_type_display()} - {self.name}"

class ClothingProduct(models.Model):
    CONDITION_CHOICES = [
        ('new', 'new'),
        ('used', 'used'),
    ]
    
    MATERIAL_CHOICES = [
        ('cotton', 'cotton'),
        ('polyester', 'polyester'),
        ('wool', 'wool'),
        ('silk', 'silk'),
        ('denim', 'denim'),
        ('leather', 'leather'),
        ('mixed', 'mixed'),
    ]
    
    # Basic info
    name = models.CharField(max_length=200, verbose_name='product name')
    brand = models.ForeignKey(ClothingBrand, on_delete=models.CASCADE, verbose_name='brand')
    category = models.ForeignKey(ClothingCategory, on_delete=models.CASCADE, verbose_name='category')
    collection_year = models.IntegerField(verbose_name='سال مجموعه', validators=[MinValueValidator(2000), MaxValueValidator(2030)])
    
    # Technical info
    description = models.TextField(verbose_name='description')
    material = models.CharField(max_length=20, choices=MATERIAL_CHOICES, verbose_name='material')
    material_composition = models.CharField(max_length=200, verbose_name='material composition', blank=True)
    care_instructions = models.TextField(verbose_name='care instructions', blank=True)
    
    # Price and Count
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='price')
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='price with discount', null=True, blank=True)
    sku = models.CharField(max_length=50, unique=True, verbose_name='product code')
    
    # condition
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, verbose_name='condition')
    is_active = models.BooleanField(default=True, verbose_name='active')
    is_featured = models.BooleanField(default=False, verbose_name='featured')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'name of product'
        verbose_name_plural = 'name of products'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.brand.name} {self.name}"

class Size(models.Model):
    SIZE_TYPES = [
        ('clothing', 'clothing'),
        ('shoes', 'shoes'),
        ('accessory', 'accessory'),
    ]
    
    name = models.CharField(max_length=50, verbose_name='size')
    size_type = models.CharField(max_length=20, choices=SIZE_TYPES, verbose_name='size type')
    description = models.CharField(max_length=100, verbose_name='description', blank=True)
    
    class Meta:
        verbose_name = 'size'
        verbose_name_plural = 'sizs'
    
    def __str__(self):
        return f"{self.name} ({self.get_size_type_display()})"

class Color(models.Model):
    name = models.CharField(max_length=50, verbose_name='color name')
    hex_code = models.CharField(max_length=7, verbose_name='HEX Code', blank=True)
    
    class Meta:
        verbose_name = 'color'
        verbose_name_plural = 'colors'
    
    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(ClothingProduct, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, verbose_name='size')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, verbose_name='color')
    stock = models.IntegerField(verbose_name='stock', default=0)
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='price modifier')
    
    class Meta:
        verbose_name = 'product variant'
        verbose_name_plural = 'products variant'
        unique_together = ['product', 'size', 'color']
    
    def __str__(self):
        return f"{self.product.name} - {self.size.name} - {self.color.name}"
    
    def final_price(self):
        return self.product.price + self.price_modifier

class ClothingProductImage(models.Model):
    product = models.ForeignKey(ClothingProduct, on_delete=models.CASCADE, related_name='images')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='variant_images')
    image = models.ImageField(upload_to='clothing/products/images/')
    alt_text = models.CharField(max_length=100, verbose_name='alt text', blank=True)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, null=True, blank=True, verbose_name='colors')
    is_main = models.BooleanField(default=False, verbose_name='main image')
    
    class Meta:
        verbose_name = 'image'
        verbose_name_plural = 'iamges'
    
    def __str__(self):
        return f"Image for {self.product.name}"