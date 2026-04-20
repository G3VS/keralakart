"""
Run this once after migrations to populate KeralaKart with sample data.
Usage: python manage.py shell < seed_data.py
"""

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keralakart.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Category, Vendor, Product

# ── Categories ────────────────────────────────────────────────────────────────
categories = [
    ('Spices & Condiments',   'spices-condiments',   '🫙'),
    ('Handicrafts & Decor',   'handicrafts-decor',   '🪔'),
    ('Handloom & Textiles',   'handloom-textiles',   '🧵'),
    ('Ayurveda & Wellness',   'ayurveda-wellness',   '🌱'),
    ('Kerala Foods',          'kerala-foods',        '🍛'),
    ('Religious Items',       'religious-items',     '🙏'),
    ('Natural Beauty',        'natural-beauty',      '✨'),
    ('Organic Produce',       'organic-produce',     '🥥'),
]

for name, slug, icon in categories:
    cat, created = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'icon': icon})
    if created:
        print(f'  ✓ Category: {name}')

# ── Admin user ────────────────────────────────────────────────────────────────
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@keralakart.com', 'admin123')
    print('  ✓ Superuser: admin / admin123')

# ── Sample vendor ─────────────────────────────────────────────────────────────
if not User.objects.filter(username='vendor1').exists():
    u = User.objects.create_user('vendor1', 'vendor1@example.com', 'vendor123')
    vendor = Vendor.objects.create(
        user=u,
        shop_name='Wayanad Spice Garden',
        location='Wayanad',
        description='Premium spices directly from our farm in Wayanad. Organic and sun-dried.',
        status='approved',
    )
    print('  ✓ Vendor: vendor1 / vendor123')

    # Sample products
    spices = Category.objects.get(slug='spices-condiments')
    foods  = Category.objects.get(slug='kerala-foods')
    ayur   = Category.objects.get(slug='ayurveda-wellness')

    sample_products = [
        dict(name='Idukki Cardamom — Premium Grade A', category=spices,
             description='Hand-picked green cardamom from the misty hills of Idukki. Rich aroma, bold flavour. Perfect for chai, biryanis, and sweets.',
             price=480, original_price=600, stock=150, weight='100g', origin='Idukki'),
        dict(name='Wayanad Black Pepper — Whole', category=spices,
             description='Bold, pungent black pepper grown in the forests of Wayanad. Sun-dried and unprocessed for maximum potency.',
             price=320, original_price=400, stock=200, weight='250g', origin='Wayanad'),
        dict(name='Organic Turmeric Powder', category=spices,
             description='Stone-ground turmeric from Kerala farms. High curcumin content, deep golden colour. No preservatives.',
             price=160, original_price=None, stock=300, weight='200g', origin='Ernakulam'),
        dict(name='Kerala Banana Chips — Coconut Oil', category=foods,
             description='Traditional Kerala-style banana chips fried in pure coconut oil. Crispy, golden, and irresistible.',
             price=120, original_price=150, stock=400, weight='250g', origin='Thrissur'),
        dict(name='Coconut Oil — Cold Pressed Virgin', category=ayur,
             description='Cold-pressed virgin coconut oil from fresh Kerala coconuts. Ideal for cooking, hair care, and skin care.',
             price=380, original_price=450, stock=100, weight='500ml', origin='Alappuzha'),
        dict(name='Dried Ginger — Chukku', category=spices,
             description='Sun-dried Kerala ginger (chukku). Used in herbal teas, ayurvedic preparations, and traditional cooking.',
             price=140, original_price=None, stock=250, weight='100g', origin='Kozhikode'),
    ]

    for pd in sample_products:
        Product.objects.create(vendor=vendor, is_featured=True, **pd)
        print(f'  ✓ Product: {pd["name"]}')

# ── Sample buyer ──────────────────────────────────────────────────────────────
if not User.objects.filter(username='buyer1').exists():
    User.objects.create_user('buyer1', 'buyer1@example.com', 'buyer123')
    print('  ✓ Buyer: buyer1 / buyer123')

print('\n🌿 KeralaKart seeded successfully!')
print('\nTest accounts:')
print('  Admin:  admin / admin123  →  /admin/')
print('  Vendor: vendor1 / vendor123  →  /dashboard/')
print('  Buyer:  buyer1 / buyer123  →  /')
