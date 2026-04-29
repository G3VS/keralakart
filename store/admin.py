from django.contrib import admin
from .models import Category, Vendor, Product, Order, OrderItem, Review, Wishlist

admin.site.site_header = 'KeralaKart Admin'
admin.site.site_title = 'KeralaKart'
admin.site.index_title = 'Marketplace Management'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'user', 'location', 'status', 'joined_at']
    list_filter = ['status', 'location']
    search_fields = ['shop_name', 'user__username']
    list_editable = ['status']
    actions = ['approve_vendors', 'reject_vendors']

    def approve_vendors(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f'{queryset.count()} vendor(s) approved.')
    approve_vendors.short_description = 'Approve selected vendors'

    def reject_vendors(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f'{queryset.count()} vendor(s) rejected.')
    reject_vendors.short_description = 'Reject selected vendors'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'category', 'price', 'stock', 'is_active', 'is_featured']
    list_filter = ['is_active', 'is_featured', 'category']
    search_fields = ['name', 'vendor__shop_name']
    list_editable = ['is_active', 'is_featured', 'price', 'stock']
    prepopulated_fields = {'slug': ('name',)}

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'buyer', 'status', 'payment_method', 'is_paid', 'created_at']
    list_filter = ['status', 'payment_method', 'is_paid']
    search_fields = ['buyer__username', 'full_name', 'email']
    list_editable = ['status', 'is_paid']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'created_at']
    list_filter = ['rating']
