from django.contrib import admin
from .models import Menu, Booking, Category, Rating, Order


# Register your models here.
admin.site.register(Menu)
admin.site.register(Category)
admin.site.register(Booking)
admin.site.register(Rating)
admin.site.register(Order)


