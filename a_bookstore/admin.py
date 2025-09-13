from django.contrib import admin

from a_bookstore.models import Category, Book, BookImage, Author, Publisher, DigitalBook, PaperQuality, PrintingQuality, BookSpecification, Review


admin.site.register(Category)
admin.site.register(Book)
admin.site.register(BookImage)
admin.site.register(Author)
admin.site.register(Publisher)
admin.site.register(DigitalBook)
admin.site.register(PaperQuality)
admin.site.register(PrintingQuality)
admin.site.register(BookSpecification)
admin.site.register(Review)