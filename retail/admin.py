from .models import Product, Stock, Sale, StockTransaction, Organization, UserProfile
from django.contrib import admin

admin.site.register(Product)
admin.site.register(Stock)
admin.site.register(Sale)
admin.site.register(StockTransaction)
admin.site.register(Organization)
admin.site.register(UserProfile)
