from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('vendor/<slug:slug>/', views.vendor_detail, name='vendor_detail'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),

    # Orders
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.my_orders, name='my_orders'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:pk>/', views.toggle_wishlist, name='toggle_wishlist'),

    # Vendor
    path('vendor-register/', views.vendor_register, name='vendor_register'),
    path('dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('dashboard/product/add/', views.product_add, name='product_add'),
    path('dashboard/product/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('dashboard/product/delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('dashboard/order/<int:pk>/status/', views.update_order_status, name='update_order_status'),

    # Razorpay payment
    path('payment/create-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('payment/verify/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),

    # API test 
    path('api/test/', views.test_api),
    path('api/products/', views.product_list_api),
]
