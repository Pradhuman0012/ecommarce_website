from django.db.models.signals import post_save
from django.dispatch import receiver

from billing.models import Bill
from orders.models import OrderHistory


@receiver(post_save, sender=Bill)
def create_order_history_from_bill(sender, instance: Bill, **kwargs):
    """
    Create history ONLY when bill has an order
    and history does not already exist.
    """

    # Bill must be linked to order
    if not hasattr(instance, "order"):
        return

    # Prevent duplicates
    if OrderHistory.objects.filter(order=instance.order).exists():
        return

    OrderHistory.objects.create(
        order=instance.order,
        bill_number=instance.bill_number,
        customer_name=instance.customer_name,
        customer_phone=instance.customer_phone,
        payment_mode=instance.payment_mode,
        subtotal=instance.subtotal(),
        discount=instance.discount_amount,
        gst=instance.gst_amount(),
        total_amount=instance.total_amount(),
        cash_received=instance.cash_received,
        change_returned=instance.change_returned,
        bill_pdf_path=instance.bill_pdf_path or "",
        items_snapshot=[
            {
                "item_name": bi.item.name,
                "quantity": bi.quantity,
                "price": str(bi.price),
            }
            for bi in instance.items.all()
        ],
    )
