from django.contrib import admin
from .models import Item, OrderedItems, Order, BillingAddress

admin.site.register(Item)
admin.site.register(OrderedItems)
admin.site.register(Order)
admin.site.register(BillingAddress)
