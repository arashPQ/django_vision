from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey


'''

    This Category for mega menu, advanced Categorize for products. You can use this category model for other projects
    Example :
    
        Computer & IT
            Software Development
                Python language
                    Django
            Networking
                CCNA
                ...
            ...

'''


class Category(MPTTModel):
    name = models.CharField(max_length=128, db_index=True)
    slug = models.SlugField(max_length=128, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE,
                            null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='catefories/', blank=True)
    
    class MPTTMeta:
        order_insertion_by = ['name']
        
    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("shop:product_list_by_category", args=[self.slug])
    
    
class Publisher(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='publishers/')
    
    def __str__(self):
        return self.name
    

class Author(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='authors/', blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    
    
    def __str__(self):
        return self.name


class Book(models.Model):
    BOOK_TYPE_CHOICES = [
        ('physical', 'physical'),
        ('digital', 'digital'),
        ('both', 'both'),
    ]
    
    BINDING_CHOICES = [
        ('hardcover', 'hardcover'),
        ('paperback', 'paperback'),
        ('spiral', ' spiral'),
        ('ebook', 'ebook'),
    ]
    
    LANGUAGE_CHOICES = [
        ('persian', 'persian'),
        ('english', 'english'),
        ('swedish', 'swedish'),
        ('other', 'other'),
    ]

    # Base info
    title = models.CharField(max_length=254)
    slug = models.SlugField(max_length=254, unique=True)
    author = models.ManyToManyField(Author, related_name='books')
    translator = models.ManyToManyField(Author, related_name='translated_books', blank=True)
    publisher = models.ForeignKey(Publisher, related_name='books', on_delete=models.CASCADE)
    category = models.ManyToManyField(Category, related_name='books')
    
    # Technical info
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True)
    isbn_digital = models.CharField(max_length=13, blank=True, null=True, verbose_name='ISBN digital')
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='english')
    book_type = models.CharField(max_length=10, choices=BOOK_TYPE_CHOICES)
    binding = models.CharField(max_length=10, choices=BINDING_CHOICES, blank=True)
    
    # appearance info
    cover_image = models.ImageField(upload_to='books/covers/')
    images = models.ManyToManyField('BookImage', blank=True, related_name='book_with_additionals')
    dimensions = models.CharField(max_length=50, blank=True, help_text='length x width x height (cm)')
    weight = models.PositiveIntegerField(blank=True, null=True, help_text='weight')
    
    # Detail info
    description = models.TextField()
    table_of_contents = models.TextField(blank=True, verbose_name='table of contents')
    pages = models.PositiveIntegerField()
    publication_date = models.DateField()
    edition = models.PositiveIntegerField(default=1, verbose_name='edition')
    
    # Price and stock
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    digital_stock = models.BooleanField(default=True, verbose_name='digital stock')
    
    # Status
    available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    best_seller = models.BooleanField(default=False)
    new_release = models.BooleanField(default=False)
    
    # Meta info
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created',)
        indexes = [models.Index(fields=['id', 'slug'])]

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])
    
    @property
    def current_price(self):
        return self.discount_price if self.discount_price else self.base_price
    
    @property
    def discount_percentage(self):
        if self.discount_price:
            return int(((self.base_price - self.discount_price) / self.base_price) * 100)
        return 0
    

class BookImage(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='books/images/')
    alt_text = models.CharField(max_length=64, blank=True)
    is_feautered = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"image for {self.book.title}"
    


class PaperQuality(models.Model):
    PAPER_TYPE_CHOICES = [
        ('glossy', 'glossy'),
        ('matte', 'matte'),
        ('cream', 'cream'),
        ('white', 'white'),
        ('recycled', 'recycled'),
    ]
    
    name = models.CharField(max_length=100)
    paper_type = models.CharField(max_length=10, choices=PAPER_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_paper_weight_display()})"


class PrintingQuality(models.Model):
    PRINT_TYPE_CHOICES = [
        ('bw', 'black & white'),
        ('color', 'colored'),
        ('mixed', 'mixed'),
    ]
    
    PRINT_QUALITY_CHOICES = [
        ('standard', 'standard'),
        ('premium', 'premium'),
        ('luxury', 'luxury'),
    ]
    
    name = models.CharField(max_length=100)
    print_type = models.CharField(max_length=10, choices=PRINT_TYPE_CHOICES)
    print_quality = models.CharField(max_length=10, choices=PRINT_QUALITY_CHOICES)
    color_accuracy = models.CharField(max_length=100, blank=True)
    resolution = models.CharField(max_length=50, blank=True, help_text='example: 1200 DPI')
    
    def __str__(self):
        return f"{self.name} - {self.get_print_type_display()}"


class DigitalBook(models.Model):
    FILE_FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('epub', 'EPUB'),
        ('mobi', 'MOBI'),
        ('azw3', 'AZW3'),
    ]
    
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='digital_version')
    file_format = models.CharField(max_length=5, choices=FILE_FORMAT_CHOICES, default='pdf')
    file = models.FileField(upload_to='books/digital/')
    file_size = models.PositiveIntegerField(help_text="example: 12 MB")
    watermark = models.BooleanField(default=True)
    drm_protected = models.BooleanField(default=False)
    download_limit = models.PositiveIntegerField(default=3)
    download_expiry = models.PositiveIntegerField(default=30)
    sample_pages = models.FileField(upload_to='books/samples/', blank=True, null=True)
    
    download_count = models.PositiveIntegerField(default=0)
    last_download = models.DateTimeField(blank=True, null=True)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Digital: {self.book.title}"
    
    
class BookSpecification(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='specifications')
    paper_quality = models.ForeignKey(PaperQuality, on_delete=models.SET_NULL, null=True, blank=True)
    printing_quality = models.ForeignKey(PrintingQuality, on_delete=models.SET_NULL, null=True, blank=True)
    
    # cover material
    cover_material = models.CharField(max_length=100, blank=True)
    cover_finish = models.CharField(max_length=100, blank=True)
    
    # binding type
    binding_type = models.CharField(max_length=100, blank=True)
    binding_durability = models.CharField(max_length=100, blank=True)
    
    # etc technical info
    ink_type = models.CharField(max_length=100, blank=True, help_text='ink type')
    environmental_friendly = models.BooleanField(default=False, verbose_name='environmental friendly')
    made_in = models.CharField(max_length=100, blank=True, verbose_name='made in ...')
    
    # warranty_period
    warranty_period = models.CharField(max_length=50, blank=True, help_text='example: 6 months')
    return_policy = models.TextField(blank=True, help_text='return policy')
    
    def __str__(self):
        return f"Specs for {self.book.title}"


class Review(models.Model):
    book = models.ForeignKey(Book, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=100)
    comment = models.TextField()
    pros = models.TextField(blank=True)
    cons = models.TextField(blank=True)
    verified_purchase = models.BooleanField(default=False, verbose_name='verified purchase')
    helpful_yes = models.PositiveIntegerField(default=0)
    helpful_no = models.PositiveIntegerField(default=0)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['book', 'user']
        ordering = ('-created',)
    
    def __str__(self):
        return f"Review by {self.user} for {self.book.title}"
        