from django.contrib import admin
from .models import Item, OrderedItems, Order, BillingAddress, Payment

admin.site.register(Item)


class OrderedItemsAdmin(admin.ModelAdmin):
    list_display = ['item', 'user', 'timestamp']


admin.site.register(OrderedItems, OrderedItemsAdmin)


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user',  'user', 'timestamp']


admin.site.register(Order, OrderAdmin)
admin.site.register(BillingAddress)
admin.site.register(Payment)
