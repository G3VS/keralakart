from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Product, Category, Vendor, Order, OrderItem, Review, Wishlist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import razorpay
import json
from django.conf import settings

# ─── Cart helpers (session-based) ────────────────────────────────────────────

def get_cart(request):
    return request.session.get('cart', {})

def save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


# ─── Public pages ─────────────────────────────────────────────────────────────

def home(request):
    featured = Product.objects.filter(is_active=True, is_featured=True)[:8]
    categories = Category.objects.all()
    latest = Product.objects.filter(is_active=True)[:8]
    vendors = Vendor.objects.filter(status='approved')[:6]
    return render(request, 'store/home.html', {
        'featured': featured,
        'categories': categories,
        'latest': latest,
        'vendors': vendors,
    })


def product_list(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()

    q = request.GET.get('q', '')
    cat_slug = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort = request.GET.get('sort', '')

    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(origin__icontains=q) |
            Q(vendor__shop_name__icontains=q)
        )
    if cat_slug:
        products = products.filter(category__slug=cat_slug)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')

    active_category = categories.filter(slug=cat_slug).first() if cat_slug else None

    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'q': q,
        'cat_slug': cat_slug,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'active_category': active_category,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:4]
    reviews = product.reviews.all().order_by('-created_at')
    user_review = None
    in_wishlist = False
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        if 'review_submit' in request.POST:
            if not user_review:
                Review.objects.create(
                    product=product,
                    user=request.user,
                    rating=request.POST.get('rating', 5),
                    comment=request.POST.get('comment', '')
                )
                messages.success(request, 'Review submitted!')
            return redirect('product_detail', slug=slug)

    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
        'reviews': reviews,
        'user_review': user_review,
        'in_wishlist': in_wishlist,
    })


def vendor_detail(request, slug):
    vendor = get_object_or_404(Vendor, slug=slug, status='approved')
    products = vendor.products.filter(is_active=True)
    return render(request, 'store/vendor_detail.html', {
        'vendor': vendor,
        'products': products,
    })


# ─── Cart ─────────────────────────────────────────────────────────────────────

def cart_view(request):
    cart = get_cart(request)
    items = []
    total = 0
    for pid, qty in cart.items():
        try:
            p = Product.objects.get(pk=pid)
            subtotal = p.price * qty
            total += subtotal
            items.append({'product': p, 'quantity': qty, 'subtotal': subtotal})
        except Product.DoesNotExist:
            pass
    return render(request, 'store/cart.html', {'items': items, 'total': total})


def add_to_cart(request, pk):
    cart = get_cart(request)
    pid = str(pk)
    cart[pid] = cart.get(pid, 0) + 1
    save_cart(request, cart)
    messages.success(request, 'Added to cart!')
    return redirect(request.META.get('HTTP_REFERER', 'cart'))

@login_required
def buy_now(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    
    if product.stock == 0:
        messages.error(request, 'Sorry this product is out of stock.')
        return redirect('product_detail', slug=product.slug)
    
    # Store buy now item separately in session
    request.session['buy_now'] = {
        'product_id': pk,
        'quantity':   1,
    }
    request.session.modified = True
    
    return redirect('buy_now_checkout')


@login_required
def buy_now_checkout(request):
    buy_now = request.session.get('buy_now')
    
    if not buy_now:
        messages.warning(request, 'No product selected for direct purchase.')
        return redirect('product_list')
    
    try:
        product  = Product.objects.get(pk=buy_now['product_id'])
        quantity = buy_now.get('quantity', 1)
        subtotal = product.price * quantity
        total    = subtotal
    except Product.DoesNotExist:
        messages.error(request, 'Product not found.')
        return redirect('product_list')

    items = [{'product': product, 'quantity': quantity, 'subtotal': subtotal}]

    if request.method == 'POST':
        order = Order.objects.create(
            buyer          = request.user,
            full_name      = request.POST['full_name'],
            email          = request.POST['email'],
            phone          = request.POST['phone'],
            address_line1  = request.POST['address_line1'],
            address_line2  = request.POST.get('address_line2', ''),
            city           = request.POST['city'],
            state          = request.POST.get('state', 'Kerala'),
            pincode        = request.POST['pincode'],
            country        = request.POST.get('country', 'India'),
            payment_method = request.POST.get('payment_method', 'COD'),
            is_paid        = False,
        )

        OrderItem.objects.create(
            order    = order,
            product  = product,
            quantity = quantity,
            price    = product.price,
        )

        # Clear buy now session
        if 'buy_now' in request.session:
            del request.session['buy_now']
            request.session.modified = True

        # COD — redirect immediately
        if order.payment_method == 'COD':
            messages.success(request, f'Order #{order.pk} placed successfully!')
            return redirect('order_detail', pk=order.pk)

        # Razorpay — return JSON for frontend
        return JsonResponse({
            'order_id': order.pk,
            'total':    float(total),
        })

    return render(request, 'store/buy_now_checkout.html', {
        'items':   items,
        'total':   total,
        'product': product,
        'user':    request.user,
    })

def remove_from_cart(request, pk):
    cart = get_cart(request)
    pid = str(pk)
    if pid in cart:
        del cart[pid]
        save_cart(request, cart)
    return redirect('cart')


def update_cart(request, pk):
    cart = get_cart(request)
    pid = str(pk)
    qty = int(request.POST.get('quantity', 1))
    if qty > 0:
        cart[pid] = qty
    else:
        cart.pop(pid, None)
    save_cart(request, cart)
    return redirect('cart')


# ─── Checkout & Orders ────────────────────────────────────────────────────────

@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    items = []
    total = 0
    for pid, qty in cart.items():
        try:
            p = Product.objects.get(pk=pid)
            subtotal = p.price * qty
            total += subtotal
            items.append({'product': p, 'quantity': qty, 'subtotal': subtotal})
        except Product.DoesNotExist:
            pass

    if request.method == 'POST':
        # Create the order
        order = Order.objects.create(
            buyer=request.user,
            full_name=request.POST['full_name'],
            email=request.POST['email'],
            phone=request.POST['phone'],
            address_line1=request.POST['address_line1'],
            address_line2=request.POST.get('address_line2', ''),
            city=request.POST['city'],
            state=request.POST.get('state', 'Kerala'),
            pincode=request.POST['pincode'],
            country=request.POST.get('country', 'India'),
            payment_method=request.POST.get('payment_method', 'COD'),
            is_paid=False,  # Will be set to True after Razorpay verification
        )
        
        # Create order items
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price,
            )
        
        # If COD, clear cart and redirect
        if order.payment_method == 'COD':
            request.session['cart'] = {}
            messages.success(request, f'Order #{order.pk} placed successfully! 🎉')
            return redirect('order_detail', pk=order.pk)
        
        # If Razorpay, return order ID to frontend (handled by JS)
        # Don't clear cart yet — only after payment succeeds
        return JsonResponse({'order_id': order.pk, 'total': float(total)})

    return render(request, 'store/checkout.html', {
        'items': items,
        'total': total,
        'user': request.user,
    })

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, buyer=request.user)
    return render(request, 'store/order_detail.html', {'order': order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(buyer=request.user)
    return render(request, 'store/my_orders.html', {'orders': orders})


# ─── Wishlist ─────────────────────────────────────────────────────────────────

@login_required
def toggle_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
        messages.info(request, 'Removed from wishlist.')
    else:
        messages.success(request, 'Added to wishlist!')
    return redirect(request.META.get('HTTP_REFERER', 'product_detail'))


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'store/wishlist.html', {'items': items})


# ─── Vendor dashboard ─────────────────────────────────────────────────────────

@login_required
def vendor_dashboard(request):
    try:
        vendor = request.user.vendor
    except Vendor.DoesNotExist:
        return redirect('vendor_register')

    products = vendor.products.all()
    orders = OrderItem.objects.filter(product__vendor=vendor).select_related('order').order_by('-order__created_at')[:20]

    return render(request, 'store/vendor_dashboard.html', {
        'vendor': vendor,
        'products': products,
        'orders': orders,
        'revenue': vendor.total_revenue(),
        'sales': vendor.total_sales(),
    })


@login_required
def vendor_register(request):
    """Modified to fix the district list error"""
    if hasattr(request.user, 'vendor'):
        return redirect('vendor_dashboard')
    
    # Define the districts here so they can be passed to the template
    districts = [
        "Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha", 
        "Kottayam", "Idukki", "Ernakulam", "Thrissur", "Palakkad", 
        "Malappuram", "Kozhikode", "Wayanad", "Kannur", "Kasaragod"
    ]

    if request.method == 'POST':
        Vendor.objects.create(
            user=request.user,
            shop_name=request.POST['shop_name'],
            description=request.POST.get('description', ''),
            location=request.POST['location'],
            phone=request.POST.get('phone', ''),
        )
        messages.success(request, 'Shop registered! Awaiting admin approval.')
        return redirect('vendor_dashboard')
        
    return render(request, 'store/vendor_register.html', {'districts': districts})


@login_required
def product_add(request):
    try:
        vendor = request.user.vendor
        if vendor.status != 'approved':
            messages.warning(request, 'Your shop is pending approval.')
            return redirect('vendor_dashboard')
    except Vendor.DoesNotExist:
        return redirect('vendor_register')

    categories = Category.objects.all()
    if request.method == 'POST':
        product = Product.objects.create(
            vendor=vendor,
            category=Category.objects.get(pk=request.POST['category']),
            name=request.POST['name'],
            description=request.POST['description'],
            price=request.POST['price'],
            original_price=request.POST.get('original_price') or None,
            stock=request.POST.get('stock', 0),
            weight=request.POST.get('weight', ''),
            origin=request.POST.get('origin', ''),
            image=request.FILES.get('image'),
        )
        messages.success(request, f'"{product.name}" listed successfully!')
        return redirect('vendor_dashboard')
    return render(request, 'store/product_form.html', {'categories': categories, 'action': 'Add'})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor)
    categories = Category.objects.all()
    if request.method == 'POST':
        product.name = request.POST['name']
        product.description = request.POST['description']
        product.price = request.POST['price']
        product.original_price = request.POST.get('original_price') or None
        product.stock = request.POST.get('stock', 0)
        product.weight = request.POST.get('weight', '')
        product.origin = request.POST.get('origin', '')
        product.category = Category.objects.get(pk=request.POST['category'])
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        product.save()
        messages.success(request, 'Product updated!')
        return redirect('vendor_dashboard')
    return render(request, 'store/product_form.html', {
        'categories': categories,
        'product': product,
        'action': 'Edit'
    })


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
    return redirect('vendor_dashboard')


@login_required
def update_order_status(request, pk):
    item = get_object_or_404(OrderItem, pk=pk, product__vendor=request.user.vendor)
    if request.method == 'POST':
        item.order.status = request.POST['status']
        item.order.save()
        messages.success(request, 'Order status updated.')
    return redirect('vendor_dashboard')

@login_required
def create_razorpay_order(request):
    """Step 1: Create Razorpay order and return credentials to frontend"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            django_order_id = data.get('order_id')
            total_amount = data.get('total')
            
            if not django_order_id or not total_amount:
                return JsonResponse({'error': 'Missing order details'}, status=400)
            
            # Amount in paise (Razorpay uses smallest currency unit)
            amount_paise = int(float(total_amount) * 100)
            
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            
            # Create Razorpay order
            razorpay_order = client.order.create({
                'amount': amount_paise,
                'currency': 'INR',
                'receipt': f'order_{django_order_id}',
                'payment_capture': 1
            })
            
            return JsonResponse({
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'amount': amount_paise,
                'currency': 'INR',
                'django_order_id': django_order_id,
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def verify_razorpay_payment(request):
    """Step 2: Verify payment signature and mark order as paid"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            
            # Verify signature
            params_dict = {
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature'],
            }
            
            client.utility.verify_payment_signature(params_dict)
            
            # Payment verified — update Django order
            order_id = data.get('django_order_id')
            # ✅ Just find by ID — safer
            order = Order.objects.get(pk=data['django_order_id'])
            order.is_paid = True
            order.status = 'confirmed'
            order.save()
            
            # Clear the cart
            request.session['cart'] = {}
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'order_id': order.pk,
                'message': 'Payment successful!'
            })
            
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({
                'status': 'failed',
                'error': 'Invalid payment signature'
            }, status=400)
        except Order.DoesNotExist:
            return JsonResponse({
                'status': 'failed',
                'error': 'Order not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)
# Inside your views.py (the function that handles the return/callback)
def payment_success(request):
    # 1. Get the order ID from the URL or session
    order_id = request.GET.get('order_id')
    order = Order.objects.get(id=order_id)
    
    # 2. UPDATE THE STATUS HERE
    order.status = 'Paid'  # Make sure 'Paid' matches your model choices
    order.is_paid = True   # If you have a boolean field for payment
    order.save()
    
    return render(request, 'success.html', {'order': order})

@login_required
def payment_failed(request):
    """Handle failed/cancelled payments"""
    messages.error(request, 'Payment was cancelled or failed. Please try again.')
    return redirect('cart')

def test_api(request):
    return JsonResponse({"message": "API working!"})

def product_list_api(request):
    products = Product.objects.all()

    data = []
    for p in products:
        data.append({
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
        })

    return JsonResponse(data, safe=False)