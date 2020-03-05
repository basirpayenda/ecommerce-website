import stripe
from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, Item, OrderedItems, Address, Payment, Coupon, Refund
from django.views.generic import ListView, DetailView, View
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from .forms import CheckoutForm, RefundForm
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from .forms import CouponForm
import string
import random
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


def create_reference_code():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=20))


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


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
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'form': form, 'order': order,
                       'coupon_form': CouponForm()}
            shipping_address = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address.exists():
                context.update(
                    {'default_shipping_address': shipping_address[0]})

            billing_address = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address.exists():
                context.update(
                    {'default_billing_address': billing_address[0]})

            return render(self.request, 'checkout.html', context)
        except ObjectDoesNotExist:
            messages.success(self.request, 'Object doesn\'t exist!')
            return redirect('core:checkout')

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get(
                    "use_default_shipping")

                if use_default_shipping:
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        order.shipping_address = address_qs[0]
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available.")
                        return redirect('core:checkout')
                else:
                    shipping_address = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    payment_option = form.cleaned_data.get('payment_option')
                    shipping_address = Address.objects.create(
                        user=self.request.user,
                        street_address=shipping_address,
                        apartment_address=shipping_address2,
                        country=shipping_country,
                        zip_code=shipping_zip,
                        address_type='S'
                    )

                    order.shipping_address = shipping_address
                    order.save()

                    set_default_shipping = form.cleaned_data.get(
                        'set_default_shipping')
                    if set_default_shipping:
                        shipping_address.default = True
                        shipping_address.save()

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip_code=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")
                    # TODO: add redirect to selected payment option
                    if payment_option == 'stripe':
                        return redirect('core:payment')
                    elif payment_option == 'paypal':
                        return redirect('core:payment')
                    else:
                        messages.warning(
                            self.request, "Invalid payment option selected")
                        return redirect('core:checkout')

            return redirect('core:payment')
        except ObjectDoesNotExist:
            messages.warning(self.request, 'Object doesn\'t exist')
            return redirect('core:order-summary')


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            return render(self.request, 'payment.html')
        else:
            messages.warning(
                self.request, 'Please proceed to checkout first!')
            return redirect('core:checkout')

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
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = amount
            payment.save()
            order.payment = payment
            for item in order.items.all():
                item.ordered = True
                item.ordered = True
                item.save()
            order.ref_code = create_reference_code()
            order.save()
            messages.success(self.request, 'Your order was successful!')
            return redirect('/')
        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, f"{err.get('message')}")
            return redirect('/')

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, "Rate limit error!")
            return redirect('/')

        except stripe.error.InvalidRequestError as e:
            messages.warning(self.request, "Invalid Request Error!")
            return redirect('/')

        except stripe.error.AuthenticationError as e:
            messages.warning(self.request, "Authentication Error")
            return redirect('/')

        except stripe.error.APIConnectionError as e:
            messages.warning(self.request, "Network Communication Error")
            return redirect('/')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(
                self.request, "We have been notified of this error, sorry for inconvenience. We'll fix it soon.")
            return redirect('/')
        except Exception as e:
            messages.warning(
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
            return redirect('core:home')

        order = Order.objects.create(user=request.user, ordered=False)
        order.items.add(order_item)
        order_item.quantity = request.POST.get('number')
        order_item.save()
        return redirect('core:order-summary')


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


# def get_coupon(request, code):
#     try:
#         coupon_code = Coupon.objects.get(code=code)
#         if coupon_code.exists():
#             return coupon_code
#     except ObjectDoesNotExist:
#         messages.warning(request, "Coupon code doesn't exist!")
#         return redirect('core:checkout')


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                coupon_code = Coupon.objects.get(code=code)
                if coupon_code.exists():
                    order.coupon = coupon_code
                    order.save()
                    messages.success(
                        self.request, 'Coupon added successfully!')
                    return redirect('core:checkout')
            except ObjectDoesNotExist:
                messages.info(self.request, "Coupon code doesn't exist!")
                return redirect("core:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        return render(self.request, 'request-refund.html', {'form': form})

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                print('it exists')
                order.refund_requested = True
                order.save()
                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.save()
                messages.info(self.request, 'Refund was successful!')
                return redirect('/')
            except ObjectDoesNotExist:
                messages.info(self.request, 'This order does not exist.')
                return redirect('/')
