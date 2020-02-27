from django.urls import path
from .views import (
    ItemListView,
    checkout,
    ItemDetailView,
    add_to_cart,
    remove_from_cart,
    OrderSummaryView,
    increment_cart_item,
    decrement_item
)

app_name = 'core'
urlpatterns = [
    path('product_detail/<slug:slug>/',
         ItemDetailView.as_view(), name='product_detail'),
    path('checkout/', checkout, name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('increment_item/<slug>/', increment_cart_item,
         name='increment_cart_item'),
    path('decrement_item/<slug>/', decrement_item,
         name='decrement_item'),
    path('add-to-cart/<slug>/', add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove_from_cart'),
    path('', ItemListView.as_view(), name='home'),
]
