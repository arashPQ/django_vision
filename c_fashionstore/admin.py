from django.contrib import admin

from c_fashionstore.models import ClothingBrand, ClothingCategory, Size, ClothingProduct, ClothingProductImage, Color, ProductVariant



admin.site.register(ClothingBrand)
admin.site.register(ClothingCategory)
admin.site.register(ClothingProduct)
admin.site.register(Size)
admin.site.register(Color)
admin.site.register(ProductVariant)
admin.site.register(ClothingProductImage)
