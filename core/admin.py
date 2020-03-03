from django.contrib import admin
from .models import Item, OrderedItems, Order, Address, Payment, Coupon, Refund
admin.site.register(Item)


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_granted=True)


make_refund_accepted.description = 'Update orders to refund granted!'


class OrderedItemsAdmin(admin.ModelAdmin):
    list_display = ['item', 'user', 'timestamp', 'ordered']


admin.site.register(OrderedItems, OrderedItemsAdmin)


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'timestamp',
                    'ordered',
                    'billing_address',
                    'coupon',
                    'being_delivered',
                    'received',
                    'refund_requested',
                    'refund_granted']
    list_filter = ['user',
                   'coupon',
                   'being_delivered',
                   'received',
                   'refund_requested',
                   'refund_granted']
    list_display_links = [
        'user',
        'billing_address',
        'coupon',
    ]

    actions = [make_refund_accepted]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'country',
        'zip_code',
        'timestamp',
        'address_type',
        'default'
    ]
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user',
                     'street_address',
                     'apartment_address',
                     'zip_code', ]

    class Meta:
        verbose_name_plural = 'addresses'


admin.site.register(Address, AddressAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Refund)
