from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order, OrderHistory


@receiver(post_save, sender=Order)
def create_order_history_from_bill(sender, instance, created, **kwargs):
    """
    Create immutable snapshot when order gets billed.
    """

    if created:
        return

    if not instance.bill:
        return

    if OrderHistory.objects.filter(order=instance).exists():
        return

    bill = instance.bill

    items_snapshot = []

    for oi in instance.items.select_related("item"):
        items_snapshot.append(
            {
                "item_name": oi.item.name,
                "quantity": oi.quantity,
                "size": oi.size,
                "price": str(oi.item.get_price_for_size(oi.size)),
                "notes": oi.notes,
                "priority": oi.priority,
            }
        )

    OrderHistory.objects.create(
        order=instance,
        bill_number=bill.bill_number,
        customer_name=bill.customer_name,
        customer_phone=bill.customer_phone,
        payment_mode=bill.payment_mode,
        subtotal=bill.subtotal(),
        discount=bill.discount_amount,
        gst=bill.gst_amount(),
        total_amount=bill.total_amount(),
        cash_received=bill.cash_received,
        change_returned=bill.change_returned,
        bill_pdf_path=bill.bill_pdf_path or "",
        items_snapshot=items_snapshot,
    )
