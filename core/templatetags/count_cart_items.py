from django import template
from core.models import Order

register = template.Library()


@register.filter
def count_cart_items(user):
    if user.is_authenticated:
        qs = Order.objects.filter(user=user, ordered=False)
        if qs.exists():
            total = 0
            for item in qs[0].items.all():
                total += item.quantity
            return total
    return 0
