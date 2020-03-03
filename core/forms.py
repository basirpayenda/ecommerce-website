from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': '1234 Main St', 'class': 'w-100 my-1'
    }))
    second_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Apartment or suite', 'class': 'w-100 my-1'
    }))
    country = CountryField(blank_label='(select country)').formfield(
        widget=CountrySelectWidget(attrs={'class': "custom-select d-block w-100"}))

    zip_code = forms.CharField(
        required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # billing address and save_info
    same_billing_address = forms.BooleanField(
        required=False, widget=forms.CheckboxInput())
    save_info = forms.BooleanField(
        required=False, widget=forms.CheckboxInput())
    PAYMENT_CHOICES = (
        ('stripe', 'Stripe'),
        ('paypal', 'Paypal')
    )
    # payment method
    payment_method = forms.ChoiceField(
        widget=forms.RadioSelect(), choices=PAYMENT_CHOICES)


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))


class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)
    email = forms.EmailField()
