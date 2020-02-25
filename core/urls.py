from django.urls import path
from .views import ItemListView, checkout, ItemDetailView, add_to_cart

app_name = 'core'
urlpatterns = [
    path('product_detail/<slug:slug>/',
         ItemDetailView.as_view(), name='product_detail'),
    path('checkout/', checkout, name='checkout'),
    path('add-to-cart/<slug>/', add_to_cart, name='add_to_cart'),
    path('', ItemListView.as_view(), name='home'),
]
