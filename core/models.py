from django_countries.fields import CountryField
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify


CATEGORY_CHOICE = (
    ('shirt', 'Shirt'),
    ('sportwear', 'Sport wear'),
    ('outwear', 'Outwear'),
)

LABEL_CHOICE = (
    ('primary', 'primary'),
    ('secondary', 'secondary'),
    ('danger', 'danger'),
)


class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.DecimalField(max_digits=5,
                                         decimal_places=2, verbose_name='Discount', null=True, blank=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d/')
    image_cover = models.ImageField(upload_to='products/%Y/%m/%d/')
    description = models.TextField()
    slug = models.SlugField(max_length=150, blank=True, null=True)
    category = models.CharField(max_length=15, choices=CATEGORY_CHOICE)
    label = models.CharField(max_length=10, choices=LABEL_CHOICE)
    associated_items = models.ManyToManyField("self", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        return super(Item, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:product_detail", kwargs={"slug": self.slug})

    def get_add_to_cart_url(self):
        return reverse("core:add_to_cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("core:remove_from_cart", kwargs={
            'slug': self.slug
        })


class OrderedItems(models.Model):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='ordereditems')
    quantity = models.IntegerField(default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} {self.item.title}s from {self.user}"

    def total_price_of_item(self):
        return self.quantity * self.item.price

    def total_discount_of_item(self):
        return self.quantity * self.item.discount_price

    def total_saved_after_discount(self):
        return float(self.total_price_of_item()) - float(self.total_discount_of_item())

    def total_price_of_item_after_discount(self):
        return float(self.total_price_of_item()) - float(self.total_discount_of_item())

    def final_price(self):
        if self.item.discount_price:
            return self.total_price_of_item_after_discount()
        else:
            return self.total_price_of_item()


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=25)
    items = models.ManyToManyField(OrderedItems)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(auto_now_add=True)
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey(
        'Address', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    # refund section
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def total_price(self):
        total = 0
        for item in self.items.all():
            total += item.final_price()

        if self.coupon:
            total -= self.coupon.amount
            return total
        else:
            return float(total)


ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping')
)


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=180)
    apartment_address = models.CharField(max_length=180)
    country = CountryField(multiple=False)
    zip_code = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.pk}"
