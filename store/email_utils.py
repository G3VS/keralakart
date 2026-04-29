from django.core.mail import send_mail
from django.conf import settings


def send_order_confirmation_email(order):
    """Send email to buyer when order is placed"""
    try:
        items_text = '\n'.join([
            f'  - {item.product.name} x{item.quantity} — ₹{item.subtotal()}'
            for item in order.items.all()
        ])

        delivery_text = ''
        if order.estimated_delivery:
            delivery_text = f'\nEstimated Delivery: {order.estimated_delivery.strftime("%d %B %Y")}'

        subject = f'KeralaKart — Order #{order.pk} Confirmed! 🌿'

        message = f"""
Hi {order.full_name},

Thank you for shopping with KeralaKart! Your order has been placed successfully.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORDER DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Order Number : #{order.pk}
Order Date   : {order.created_at.strftime("%d %B %Y, %I:%M %p")}
Payment      : {order.payment_method}
Status       : {order.get_status_display()}
{delivery_text}

ITEMS ORDERED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{items_text}

Total: ₹{order.total_price()}

DELIVERY ADDRESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{order.full_name}
{order.address_line1}
{order.address_line2 + chr(10) if order.address_line2 else ''}{order.city}, {order.state} — {order.pincode}
{order.country}
Phone: {order.phone}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

We will notify you when your order is shipped.

Thank you for supporting Kerala's local artisans! 🌿

Warm regards,
Team KeralaKart
        """.strip()

        send_mail(
            subject      = subject,
            message      = message,
            from_email   = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [order.email],
            fail_silently = True,
        )
        print(f'Order confirmation email sent to {order.email}')

    except Exception as e:
        print(f'Email error: {e}')


def send_status_update_email(order):
    """Send email to buyer when order status changes"""
    try:
        status_messages = {
            'confirmed': ('Your order has been confirmed! ✅',
                         'Great news! We have confirmed your order and it is being prepared.'),
            'shipped':   ('Your order is on its way! 🚚',
                         'Your order has been shipped and is on its way to you.'),
            'delivered': ('Your order has been delivered! 🎉',
                         'Your order has been delivered. We hope you love your Kerala products!'),
            'cancelled': ('Your order has been cancelled ❌',
                         'Your order has been cancelled. If you have any questions please contact us.'),
        }

        status_info = status_messages.get(order.status)
        if not status_info:
            return

        status_title, status_body = status_info

        delivery_text = ''
        if order.estimated_delivery and order.status not in ['delivered', 'cancelled']:
            delivery_text = f'\nEstimated Delivery: {order.estimated_delivery.strftime("%d %B %Y")}'

        subject = f'KeralaKart — Order #{order.pk}: {status_title}'

        message = f"""
Hi {order.full_name},

{status_body}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORDER UPDATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Order Number : #{order.pk}
Current Status: {order.get_status_display()}
{delivery_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Thank you for shopping with KeralaKart! 🌿

Warm regards,
Team KeralaKart
        """.strip()

        send_mail(
            subject        = subject,
            message        = message,
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [order.email],
            fail_silently  = True,
        )
        print(f'Status update email sent to {order.email}')

    except Exception as e:
        print(f'Email error: {e}')