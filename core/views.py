from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, Item, OrderedItems
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse


class ItemListView(ListView):
    model = Item
    template_name = 'home.html'
    context_object_name = 'items'
    paginate_by = 9


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product_detail.html'
    context_object_name = 'item'

    def get_object(self):
        obj = get_object_or_404(Item, slug=self.kwargs.get('slug'))
        return obj

    def get_context_data(self, **kwargs):  # finally, GODDDD thanks
        item = self.get_object()
        kwargs['ordereditems'] = OrderedItems.objects.filter(
            item=item, user=self.request.user)
        return super().get_context_data(**kwargs)


def checkout(request):
    return render(request, 'checkout.html')


def add_to_cart(request, slug):
    if request.method == 'POST':
        item = get_object_or_404(Item, slug=slug)
        order_item = OrderedItems.objects.create(
            item=item,
            user=request.user,
            ordered=False
        )
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            # check if the order item is in the order
            order_item.quantity = request.POST.get('number')
            order_item.save()
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect('core:home')

        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        order_item.quantity = request.POST.get('number')
        order_item.save()
        messages.info(request, "This item was added to your cart.")
        return redirect('core:product_detail', slug=slug)


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderedItems.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect('core:product_detail', slug=slug)
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product_detail", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product_detail", slug=slug)
