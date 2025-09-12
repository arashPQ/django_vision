'''
    This is a custom user model for large projects. You can use the default Django user model for your personal projects.
    In this project, we tried to cover all the content as much as we could. For example, for a store, we cover different users such as salesperson, marketer, support, etc.
    You can choose the sections you need from them.
    And these can be present in different apps of the project. Depending on the architecture and structure of your project, you can have easier use.
    
'''

from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission, Group
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
import uuid
import logging

logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', User.UserType.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        user = self.create_user(email, password, **extra_fields)
        

        AdminProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': AdminProfile.Role.SUPERUSER,
                'security_level': AdminProfile.SecurityLevel.LEVEL_4
            }
        )
        
        return user


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='%(class)s_updated'
    )
    
    class Meta:
        abstract = True


class User(AbstractUser, TimeStampedModel):
    
    class UserType(models.TextChoices):
        CUSTOMER = 'customer', _('Customer')
        SELLER = 'seller', _('Seller')
        ADMIN = 'admin', _('Admin')
        VENDOR = 'vendor', _('Vendor')
        AFFILIATE = 'affiliate', _('Affiliate')
        SUPPORT = 'support', _('Support Agent')
    
    # We use email for login
    username = None
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    user_type = models.CharField(
        max_length=10, 
        choices=UserType.choices, 
        default=UserType.CUSTOMER,
        db_index=True
    )
    
    # User base information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    secondary_email = models.EmailField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/%Y/%m/%d/', 
        blank=True, 
        null=True,
        max_length=500
    )
    cover_photo = models.ImageField(
        upload_to='cover_photos/%Y/%m/%d/', 
        blank=True, 
        null=True,
        max_length=500
    )
    
    # User status
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_date = models.DateTimeField(blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)
    is_identity_verified = models.BooleanField(default=False)  # برای احراز هویت کامل
    account_status = models.CharField(
        max_length=20,
        choices=[
            ('active', _('Active')),
            ('suspended', _('Suspended')),
            ('banned', _('Banned')),
            ('pending', _('Pending Approval')),
            ('restricted', _('Restricted')),
        ],
        default='active',
        db_index=True
    )
    status_reason = models.TextField(blank=True, null=True)
    status_changed_date = models.DateTimeField(blank=True, null=True)
    
    # Security Settings
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_method = models.CharField(
        max_length=64,
        choices=[
            ('sms', _('SMS')),
            ('email', _('Email')),
            ('authenticator', _('Authenticator App')),
        ],
        blank=True,
        null=True
    )
    last_password_change = models.DateTimeField(auto_now_add=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    login_notifications = models.BooleanField(default=True)
    
    
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=3, default='USD')
    communication_preferences = models.JSONField(default=dict)  
    
    
    last_activity = models.DateTimeField(auto_now=True)
    login_count = models.PositiveIntegerField(default=0)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    

    credit_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The Groups this user belongs to.'),
        related_name='custom_user_set',
        related_query_name='user',
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for the user.'),
        related_name='custom_user_permissions_set',
        related_query_name='user',
    )
    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email', 'user_type']),
            models.Index(fields=['created_at', 'account_status']),
        ]
        permissions = [
            ('can_impersonate', 'Can impersonate other users'),
            ('can_export_users', 'Can export user data'),
            ('can_bulk_edit_users', 'Can bulk edit users'),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def save(self, *args, **kwargs):
        
        if self.pk:
            original = User.objects.get(pk=self.pk)
            if original.account_status != self.account_status:
                self.status_changed_date = timezone.now()
        
        # اعتبارسنجی وضعیت حساب
        if self.account_status in ['suspended', 'banned'] and not self.status_reason:
            raise ValidationError(_('Status reason is required for suspended or banned accounts.'))
        
        super().save(*args, **kwargs)
    
    @property
    def is_customer(self):
        return self.user_type == self.UserType.CUSTOMER
    
    @property
    def is_seller(self):
        return self.user_type == self.UserType.SELLER
    
    @property
    def is_admin(self):
        return self.user_type == self.UserType.ADMIN
    
    @property
    def is_vendor(self):
        return self.user_type == self.UserType.VENDOR
    
    @property
    def is_affiliate(self):
        return self.user_type == self.UserType.AFFILIATE
    
    @property
    def is_support_agent(self):
        return self.user_type == self.UserType.SUPPORT
    
    def get_display_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email.split('@')[0]
    
    def increment_login_count(self):
        self.login_count = models.F('login_count') + 1
        self.save(update_fields=['login_count'])
    
    def reset_failed_logins(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    def record_failed_login(self):
        self.failed_login_attempts = models.F('failed_login_attempts') + 1
        if self.failed_login_attempts >= 5:  # Banned after five rejected tries for 30min
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        self.save(update_fields=['failed_login_attempts', 'locked_until'])


class Address(models.Model):
    class AddressType(models.TextChoices):
        HOME = 'home', _('Home')
        WORK = 'work', _('Work')
        BILLING = 'billing', _('Billing')
        SHIPPING = 'shipping', _('Shipping')
        OTHER = 'other', _('Other')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=AddressType.choices, default=AddressType.HOME)
    is_default = models.BooleanField(default=False)
    

    street_address = models.CharField(max_length=255)
    apartment_suite = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='United States')
    
    # Geography info
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        ordering = ['-is_default', 'address_type']
    
    def __str__(self):
        return f"{self.get_address_type_display()} - {self.street_address}, {self.city}"
    
    def clean(self):
        if self.is_default:
            existing_default = Address.objects.filter(
                user=self.user, 
                address_type=self.address_type, 
                is_default=True
            ).exclude(pk=self.pk)
            if existing_default.exists():
                raise ValidationError(
                    _('There is already a default address of this type for this user.')
                )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class CustomerProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    
    gender = models.CharField(
        max_length=10,
        choices=[('male', _('Male')), ('female', _('Female')), ('other', _('Other'))],
        blank=True,
        null=True
    )
    marital_status = models.CharField(
        max_length=20,
        choices=[
            ('single', _('Single')),
            ('married', _('Married')),
            ('divorced', _('Divorced')),
            ('widowed', _('Widowed')),
        ],
        blank=True,
        null=True
    )
    occupation = models.CharField(max_length=100, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    
    '''
    preferred_categories = models.ManyToManyField(
        'catalog.Category', 
        blank=True, 
        related_name='interested_customers'
    )
    preferred_brands = models.ManyToManyField(
        'catalog.Brand', 
        blank=True, 
        related_name='preferred_by_customers'
    )
    shopping_style = models.CharField(
        max_length=20,
        choices=[
            ('budget', _('Budget Conscious')),
            ('premium', _('Premium Shopper')),
            ('bargain', _('Bargain Hunter')),
            ('impulsive', _('Impulsive Buyer')),
            ('researcher', _('Detailed Researcher')),
        ],
        blank=True,
        null=True
    )
    '''

    loyalty_tier = models.CharField(
        max_length=20,
        choices=[
            ('bronze', _('Bronze')),
            ('silver', _('Silver')),
            ('gold', _('Gold')),
            ('platinum', _('Platinum')),
            ('diamond', _('Diamond')),
        ],
        default='bronze'
    )
    loyalty_points = models.PositiveIntegerField(default=0)
    loyalty_points_earned = models.PositiveIntegerField(default=0)
    loyalty_points_spent = models.PositiveIntegerField(default=0)
    joined_loyalty_date = models.DateTimeField(blank=True, null=True)
    

    total_orders = models.PositiveIntegerField(default=0)
    total_items_purchased = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_purchase_date = models.DateTimeField(blank=True, null=True)
    first_purchase_date = models.DateTimeField(blank=True, null=True)
    

    preferred_payment_method = models.CharField(max_length=50, blank=True, null=True)
    cart_abandonment_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    return_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    

    # wishlist = models.ManyToManyField('catalog.Product', through='WishlistItem', blank=True)
    # recently_viewed = models.ManyToManyField('catalog.Product', through='RecentlyViewed', blank=True)
    

    email_marketing = models.BooleanField(default=True)
    sms_marketing = models.BooleanField(default=False)
    personalized_recommendations = models.BooleanField(default=True)
    cookie_consent = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Customer Profile')
        verbose_name_plural = _('Customer Profiles')
    
    def __str__(self):
        return f"Customer: {self.user.get_display_name()}"
    
    def update_loyalty_tier(self):
        points = self.loyalty_points
        
        if points >= 10000:
            new_tier = 'diamond'
        elif points >= 5000:
            new_tier = 'platinum'
        elif points >= 2000:
            new_tier = 'gold'
        elif points >= 500:
            new_tier = 'silver'
        else:
            new_tier = 'bronze'
        
        if new_tier != self.loyalty_tier:
            self.loyalty_tier = new_tier
            self.save(update_fields=['loyalty_tier'])
            logger.info(f"Customer {self.user.email} upgraded to {new_tier} tier")
    
    def add_loyalty_points(self, points, reason=''):

        self.loyalty_points = models.F('loyalty_points') + points
        self.loyalty_points_earned = models.F('loyalty_points_earned') + points
        self.save(update_fields=['loyalty_points', 'loyalty_points_earned'])
        
        LoyaltyHistory.objects.create(
            customer=self,
            points=points,
            balance_after=self.loyalty_points + points,
            reason=reason,
            type='earn'
        )
        
        self.update_loyalty_tier()
    
    def spend_loyalty_points(self, points, reason=''):
       
        if points > self.loyalty_points:
            raise ValueError("Not enough loyalty points")
        
        self.loyalty_points = models.F('loyalty_points') - points
        self.loyalty_points_spent = models.F('loyalty_points_spent') + points
        self.save(update_fields=['loyalty_points', 'loyalty_points_spent'])
        
        
        LoyaltyHistory.objects.create(
            customer=self,
            points=-points,
            balance_after=self.loyalty_points - points,
            reason=reason,
            type='spend'
        )


class SellerProfile(TimeStampedModel):
    class BusinessType(models.TextChoices):
        INDIVIDUAL = 'individual', _('Individual')
        SOLE_PROPRIETORSHIP = 'sole_proprietorship', _('Sole Proprietorship')
        PARTNERSHIP = 'partnership', _('Partnership')
        CORPORATION = 'corporation', _('Corporation')
        LLC = 'llc', _('Limited Liability Company')
    
    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        UNDER_REVIEW = 'under_review', _('Under Review')
        VERIFIED = 'verified', _('Verified')
        REJECTED = 'rejected', _('Rejected')
        SUSPENDED = 'suspended', _('Suspended')
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    
    
    business_name = models.CharField(max_length=255, unique=True)
    business_slug = models.SlugField(max_length=255, unique=True)
    business_type = models.CharField(max_length=20, choices=BusinessType.choices)
    business_description = models.TextField()
    business_logo = models.ImageField(upload_to='seller_logos/%Y/%m/%d/', blank=True, null=True)
    business_banner = models.ImageField(upload_to='seller_banners/%Y/%m/%d/', blank=True, null=True)
    
    
    business_phone = models.CharField(max_length=17, validators=[User.phone_regex])
    business_email = models.EmailField()
    business_website = models.URLField(blank=True, null=True)
    
   
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    vat_number = models.CharField(max_length=50, blank=True, null=True)
    business_registration_number = models.CharField(max_length=100, blank=True, null=True)
    bank_account_details = models.JSONField(blank=True, null=True)  # encrypted in practice
    payout_method = models.CharField(
        max_length=20,
        choices=[
            ('bank_transfer', _('Bank Transfer')),
            ('paypal', _('PayPal')),
            ('check', _('Check')),
            ('wire_transfer', _('Wire Transfer')),
        ],
        default='bank_transfer'
    )
    payout_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    

    verification_status = models.CharField(
        max_length=20, 
        choices=VerificationStatus.choices, 
        default=VerificationStatus.PENDING
    )
    verification_documents = models.JSONField(default=dict) 
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_sellers'
    )
    

    total_products = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    response_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    response_time = models.DurationField(blank=True, null=True) 
    

    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    transaction_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ('basic', _('Basic')),
            ('professional', _('Professional')),
            ('enterprise', _('Enterprise')),
        ],
        default='basic'
    )
    subscription_expiry = models.DateTimeField(blank=True, null=True)
    

    can_manage_products = models.BooleanField(default=True)
    can_manage_inventory = models.BooleanField(default=True)
    can_manage_pricing = models.BooleanField(default=True)
    can_manage_promotions = models.BooleanField(default=False)
    can_use_fulfillment_service = models.BooleanField(default=False)
    can_access_analytics = models.BooleanField(default=False)
    can_use_api = models.BooleanField(default=False)
    
    
    store_policies = models.JSONField(default=dict)  
    shipping_options = models.JSONField(default=list)
    return_policy = models.TextField(blank=True, null=True)
    support_policy = models.TextField(blank=True, null=True)
    
    # SEO Information
    meta_title = models.CharField(max_length=60, blank=True, null=True)
    meta_description = models.TextField(max_length=160, blank=True, null=True)
    store_keywords = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('Seller Profile')
        verbose_name_plural = _('Seller Profiles')
        permissions = [
            ('can_approve_sellers', 'Can approve seller applications'),
            ('can_manage_seller_commissions', 'Can manage seller commissions'),
            ('can_view_seller_financials', 'Can view seller financial information'),
        ]
    
    def __str__(self):
        return f"Seller: {self.business_name}"
    
    def save(self, *args, **kwargs):
        if not self.business_slug and self.business_name:
            
            self.business_slug = slugify(self.business_name)
        
        if self.business_slug:
            original_slug = self.business_slug
            counter = 1
            while SellerProfile.objects.filter(business_slug=self.business_slug).exclude(pk=self.pk).exists():
                self.business_slug = f"{original_slug}-{counter}"
                counter += 1
        
        super().save(*args, **kwargs)
    
    def approve(self, approved_by):
        
        if self.verification_status != self.VerificationStatus.VERIFIED:
            self.verification_status = self.VerificationStatus.VERIFIED
            self.verified_at = timezone.now()
            self.verified_by = approved_by
            self.save()
            
            # Send email
            logger.info(f"Seller {self.business_name} approved by {approved_by.email}")
    
    
    #   Security levels for Admins
class AdminProfile(TimeStampedModel):
    class Role(models.TextChoices):
        SUPERUSER = 'superuser', _('Superuser')
        SYSTEM_ADMIN = 'system_admin', _('System Administrator')
        CONTENT_MANAGER = 'content_manager', _('Content Manager')
        PRODUCT_MANAGER = 'product_manager', _('Product Manager')
        ORDER_MANAGER = 'order_manager', _('Order Manager')
        CUSTOMER_SUPPORT = 'customer_support', _('Customer Support')
        FINANCE_MANAGER = 'finance_manager', _('Finance Manager')
        MARKETING_MANAGER = 'marketing_manager', _('Marketing Manager')
        ANALYTICS = 'analytics', _('Analytics Specialist')
        SECURITY = 'security', _('Security Specialist')
    
    class SecurityLevel(models.IntegerChoices):
        LEVEL_1 = 1, _('Level 1 - Basic Access')
        LEVEL_2 = 2, _('Level 2 - Standard Access')
        LEVEL_3 = 3, _('Level 3 - Elevated Access')
        LEVEL_4 = 4, _('Level 4 - Administrative Access')
        LEVEL_5 = 5, _('Level 5 - Superuser Access')
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER_SUPPORT)
    security_level = models.IntegerField(choices=SecurityLevel.choices, default=SecurityLevel.LEVEL_1)
    

    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    department = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    reports_to = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='subordinates'
    )
    internal_phone = models.CharField(max_length=10, blank=True, null=True)
    office_location = models.CharField(max_length=100, blank=True, null=True)
    

    can_manage_users = models.BooleanField(default=False)
    can_manage_sellers = models.BooleanField(default=False)
    can_manage_products = models.BooleanField(default=False)
    can_manage_orders = models.BooleanField(default=False)
    can_manage_content = models.BooleanField(default=False)
    can_manage_promotions = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)
    can_manage_finances = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)
    can_access_audit_logs = models.BooleanField(default=False)
    can_manage_roles = models.BooleanField(default=False)
    

    access_restrictions = models.JSONField(default=dict)
    allowed_ip_ranges = models.JSONField(default=list)
    working_hours = models.JSONField(default=dict)
    
    #   Security options
    requires_2fa = models.BooleanField(default=True)
    last_security_training = models.DateField(blank=True, null=True)
    security_clearance = models.CharField(max_length=50, blank=True, null=True)
    access_review_date = models.DateField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('Admin Profile')
        verbose_name_plural = _('Admin Profiles')
        permissions = [
            ('can_elevate_permissions', 'Can elevate permissions temporarily'),
            ('can_audit_admin_actions', 'Can audit other admin actions'),
            ('can_manage_system_settings', 'Can manage system settings'),
        ]
    
    def __str__(self):
        return f"Admin: {self.user.get_display_name()} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):

        role_to_security_level = {
            self.Role.SUPERUSER: self.SecurityLevel.LEVEL_5,
            self.Role.SYSTEM_ADMIN: self.SecurityLevel.LEVEL_4,
            self.Role.FINANCE_MANAGER: self.SecurityLevel.LEVEL_4,
            self.Role.SECURITY: self.SecurityLevel.LEVEL_4,
            self.Role.PRODUCT_MANAGER: self.SecurityLevel.LEVEL_3,
            self.Role.ORDER_MANAGER: self.SecurityLevel.LEVEL_3,
            self.Role.MARKETING_MANAGER: self.SecurityLevel.LEVEL_3,
            self.Role.ANALYTICS: self.SecurityLevel.LEVEL_3,
            self.Role.CONTENT_MANAGER: self.SecurityLevel.LEVEL_2,
            self.Role.CUSTOMER_SUPPORT: self.SecurityLevel.LEVEL_1,
        }
        
        if self.role in role_to_security_level:
            self.security_level = role_to_security_level[self.role]
        
        # available all for SuperUser
        if self.role == self.Role.SUPERUSER:
            self.can_manage_users = True
            self.can_manage_sellers = True
            self.can_manage_products = True
            self.can_manage_orders = True
            self.can_manage_content = True
            self.can_manage_promotions = True
            self.can_view_reports = True
            self.can_manage_finances = True
            self.can_manage_settings = True
            self.can_access_audit_logs = True
            self.can_manage_roles = True
        
        super().save(*args, **kwargs)
    
    def has_permission(self, permission_code):
        permission_mapping = {
            'manage_users': self.can_manage_users,
            'manage_sellers': self.can_manage_sellers,
            'manage_products': self.can_manage_products,
            'manage_orders': self.can_manage_orders,
            'manage_content': self.can_manage_content,
            'manage_promotions': self.can_manage_promotions,
            'view_reports': self.can_view_reports,
            'manage_finances': self.can_manage_finances,
            'manage_settings': self.can_manage_settings,
            'access_audit_logs': self.can_access_audit_logs,
            'manage_roles': self.can_manage_roles,
        }
        
        return permission_mapping.get(permission_code, False)


'''
class WishlistItem(TimeStampedModel):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    priority = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    class Meta:
        unique_together = ['customer', 'product']
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.customer.user.email} - {self.product.name}"


class RecentlyViewed(TimeStampedModel):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE)
    view_count = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ['customer', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.user.email} - {self.product.name} ({self.view_count} views)"

'''
class LoyaltyHistory(TimeStampedModel):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='loyalty_history')
    points = models.IntegerField()
    balance_after = models.IntegerField()
    reason = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=[('earn', 'Earned'), ('spend', 'Spent')])
    reference_type = models.CharField(max_length=50, blank=True, null=True)
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = _('Loyalty History')
    
    def __str__(self):
        return f"{self.customer.user.email}: {self.points} points - {self.reason}"


class AdminAuditLog(TimeStampedModel):
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_actions')
    action = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Admin Audit Log')
        verbose_name_plural = _('Admin Audit Logs')
        indexes = [
            models.Index(fields=['admin', 'created_at']),
            models.Index(fields=['model', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.admin.email if self.admin else 'System'} - {self.action}"



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            if instance.user_type == User.UserType.CUSTOMER:
                CustomerProfile.objects.create(user=instance)
            elif instance.user_type == User.UserType.SELLER:
                SellerProfile.objects.create(user=instance)
            elif instance.user_type == User.UserType.ADMIN:
                AdminProfile.objects.create(user=instance)
        except Exception as e:
            logger.error(f"Error creating user profile for {instance.email}: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        if hasattr(instance, 'customer_profile'):
            instance.customer_profile.save()
        elif hasattr(instance, 'seller_profile'):
            instance.seller_profile.save()
        elif hasattr(instance, 'admin_profile'):
            instance.admin_profile.save()
    except Exception as e:
        logger.error(f"Error saving user profile for {instance.email}: {e}")


@receiver(pre_save, sender=User)
def track_user_changes(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = User.objects.get(pk=instance.pk)
            changes = {}
            

            important_fields = [
                'email', 'first_name', 'last_name', 'is_active', 
                'account_status', 'is_verified', 'user_type'
            ]
            
            for field in important_fields:
                original_value = getattr(original, field)
                new_value = getattr(instance, field)
                if original_value != new_value:
                    changes[field] = {'from': original_value, 'to': new_value}
            

            if changes:
                logger.info(f"User {instance.email} changed: {changes}")
                
        except User.DoesNotExist:
            pass


@receiver(m2m_changed)
def track_m2m_changes(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        if hasattr(instance, 'email'):
            logger.info(f"User {instance.email} had M2M change: {sender} {action}")