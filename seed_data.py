import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keralakart.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Category, Vendor, Product

print('Seeding KeralaKart...')

# ── Categories ────────────────────────────────────────────
categories_data = [
    ('Spices & Condiments', 'spices-condiments', 'bi-basket'),
    ('Handicrafts & Decor', 'handicrafts-decor', 'bi-lamp'),
    ('Handloom & Textiles', 'handloom-textiles', 'bi-scissors'),
    ('Ayurveda & Wellness', 'ayurveda-wellness', 'bi-flower1'),
    ('Kerala Foods',        'kerala-foods',      'bi-egg-fried'),
    ('Religious Items',     'religious-items',   'bi-stars'),
    ('Natural Beauty',      'natural-beauty',    'bi-droplet'),
    ('Organic Produce',     'organic-produce',   'bi-tree'),
]

for name, slug, icon in categories_data:
    cat, created = Category.objects.get_or_create(
        slug=slug,
        defaults={'name': name, 'icon': icon}
    )
    if created:
        print(f'  Created category: {name}')
    else:
        print(f'  Category exists: {name}')

# ── Admin user ────────────────────────────────────────────
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        'admin', 'admin@keralakart.com', 'admin123'
    )
    print('  Created superuser: admin / admin123')
else:
    print('  Admin already exists — skipping')

# ── Vendor ────────────────────────────────────────────────
if not User.objects.filter(username='vendor1').exists():
    u = User.objects.create_user(
        'vendor1', 'vendor1@example.com', 'vendor123'
    )
    vendor = Vendor.objects.create(
        user=u,
        shop_name='Wayanad Spice Garden',
        location='Wayanad',
        description='Premium spices directly from our farm in Wayanad.',
        status='approved',
    )
    print('  Created vendor: vendor1 / vendor123')
else:
    vendor = Vendor.objects.get(user__username='vendor1')
    print('  Vendor already exists — skipping')

# ── Products — only if none exist yet ─────────────────────
if Product.objects.filter(vendor=vendor).count() == 0:
    print('  No products found — creating sample products...')

    spices = Category.objects.get(slug='spices-condiments')
    foods  = Category.objects.get(slug='kerala-foods')
    ayur   = Category.objects.get(slug='ayurveda-wellness')

    products_data = [
        dict(
            name='Idukki Cardamom — Premium Grade A',
            category=spices,
            description='Hand-picked green cardamom from the misty hills of Idukki. Rich aroma, bold flavour.',
            price=480,
            original_price=600,
            stock=150,
            weight='100g',
            origin='Idukki'
        ),
        dict(
            name='Wayanad Black Pepper — Whole',
            category=spices,
            description='Bold pungent black pepper grown in the forests of Wayanad. Sun-dried and unprocessed.',
            price=320,
            original_price=400,
            stock=200,
            weight='250g',
            origin='Wayanad'
        ),
        dict(
            name='Organic Turmeric Powder',
            category=spices,
            description='Stone-ground turmeric from Kerala farms. High curcumin content, deep golden colour.',
            price=160,
            original_price=None,
            stock=300,
            weight='200g',
            origin='Ernakulam'
        ),
        dict(
            name='Kerala Banana Chips — Coconut Oil',
            category=foods,
            description='Traditional Kerala-style banana chips fried in pure coconut oil. Crispy and golden.',
            price=120,
            original_price=150,
            stock=400,
            weight='250g',
            origin='Thrissur'
        ),
        dict(
            name='Cold Pressed Virgin Coconut Oil',
            category=ayur,
            description='Cold-pressed from fresh Kerala coconuts. Ideal for cooking, hair and skin care.',
            price=380,
            original_price=450,
            stock=100,
            weight='500ml',
            origin='Alappuzha'
        ),
        dict(
            name='Dried Ginger — Chukku',
            category=spices,
            description='Sun-dried Kerala ginger used in herbal teas and ayurvedic preparations.',
            price=140,
            original_price=None,
            stock=250,
            weight='100g',
            origin='Kozhikode'
        ),
    ]

    for pd in products_data:
        Product.objects.create(vendor=vendor, is_featured=True, **pd)
        print(f'  Created product: {pd["name"]}')

else:
    count = Product.objects.filter(vendor=vendor).count()
    print(f'  {count} products already exist — skipping to preserve images ✅')

print('\nSeeding complete!')