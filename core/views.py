import stripe
from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, Item, OrderedItems, BillingAddress, Payment
from django.views.generic import ListView, DetailView, View
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from .forms import CheckoutForm
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY  # new


class ItemListView(ListView):
    model = Item
    template_name = 'home.html'
    context_object_name = 'items'
    paginate_by = 9


class OrderSummaryView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            return render(self.request, 'order-summary.html', {'order': order})
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class CheckoutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        return render(self.request, 'checkout.html', {'form': form})

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                second_address = form.cleaned_data.get('second_address')
                country = form.cleaned_data.get('country')
                zip_code = form.cleaned_data.get('zip_code')
                # TODO: add functionality to following:
                # same_billing_address = form.cleaned_data.get(
                #     'same_billing_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_method = form.cleaned_data.get('payment_method')
                billing_address = BillingAddress.objects.create(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=second_address,
                    country=country,
                    zip_code=zip_code
                )
                order.billing_address = billing_address
                order.save()
                # TODO: add redirect to selected payment option
                if payment_method == 'stripe':
                    return redirect('core:payment')
                elif payment_method == 'paypal':
                    return redirect('core:payment')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('core:checkout')

                messages.success(self.request, 'Checkout successfully done!')
                return redirect('core:home')
        except ObjectDoesNotExist:
            messages.warning(self.request, 'Object doesn\'t exist')
            return redirect('core:order-summary')


class PaymentView(View):
    def get(self, *args, **kwargs):
        return render(self.request, 'payment.html')

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.total_price() * 100)

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency='usd',
                source=token
            )
            order.ordered = True
            payment = Payment()
            payment.stripe_id = charge['id']
            payment.user = self.request.user
            payment.amount = amount
            payment.save()
            order.payment = payment
            for item in order.items.all():
                item.ordered = True
                item.ordered = True
                item.save()
            order.save()
            messages.success(self.request, 'Your order was successful!')
            return redirect('/')
        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f"{err.get('message')}")
            return redirect('/')

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, "Rate limit error!")
            return redirect('/')

        except stripe.error.InvalidRequestError as e:
            messages.error(self.request, "Invalid Request Error!")
            return redirect('/')

        except stripe.error.AuthenticationError as e:
            messages.error(self.request, "Authentication Error")
            return redirect('/')

        except stripe.error.APIConnectionError as e:
            messages.error(self.request, "Network Communication Error")
            return redirect('/')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(
                self.request, "We have been notified of this error, sorry for inconvenience. We'll fix it soon.")
            return redirect('/')
        except Exception as e:
            messages.error(
                self.request, "We have been notified of this exception, sorry for inconvenience. We'll fix it soon.")
            return redirect('/')


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
            item=item, user=self.request.user, ordered=False)
        return super().get_context_data(**kwargs)


def add_to_cart(request, slug):
    if request.method == 'POST':
        item = get_object_or_404(Item, slug=slug)
        order_item = OrderedItems.objects.create(
            item=item,
            user=request.user,
            ordered=False,
        )
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            # check if the order item is in the order
            order_item.quantity = request.POST.get('number')
            order_item.save()
            order.items.add(order_item)
            messages.info(
                request, "This item has been successfully added to your cart.")
            return redirect('core:home')

        order = Order.objects.create(user=request.user, ordered=False)
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
            return redirect('core:order-summary')
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:order-summary")


def increment_cart_item(request, slug):
    """ increase quantity by one """
    item = get_object_or_404(Item, slug=slug)
    order_item = OrderedItems.objects.get(
        item=item,
        user=request.user,
        ordered=False,
    )
    order_item.quantity += 1
    order_item.save()
    return redirect('core:order-summary')


def decrement_item(request, slug):
    item = get_object_or_404(Item, slug=slug)
    ordered_item = OrderedItems.objects.get(
        user=request.user, ordered=False, item=item)
    ordered_item.quantity -= 1
    ordered_item.save()
    return redirect('core:order-summary')
