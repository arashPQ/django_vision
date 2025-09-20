from django.contrib import admin

from d_homestuff.models import Category, Brand, Product, ProductAttribute, ProductAttributeValue, ProductAttributeValueThrough, ProductImage, Payment, Customer, Address, Order, OrderItem

admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(ProductAttribute)
admin.site.register(ProductAttributeValue)
admin.site.register(ProductAttributeValueThrough)
admin.site.register(ProductImage)
admin.site.register(Payment)
admin.site.register(Customer)
admin.site.register(Address)
admin.site.register(Order)
admin.site.register(OrderItem)
