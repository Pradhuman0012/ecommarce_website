import json
from decimal import Decimal
from pathlib import Path

from django.db import transaction
from django.db.models import Count

from home.models import Category, Item, ItemSize


def load_menu_from_json(json_path, clear_existing=False):
    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"{json_path} not found")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with transaction.atomic():
        if clear_existing:
            # Sirf wo items delete honge jo kisi bill mein nahi hain
            unused_items = Item.objects.annotate(bill_count=Count("billitem")).filter(
                bill_count=0
            )
            ItemSize.objects.filter(item__in=unused_items).delete()
            unused_items.delete()

            # Khali categories delete hongi
            Category.objects.annotate(item_count=Count("items")).filter(
                item_count=0
            ).delete()

        # ---------- CATEGORIES ----------
        category_map = {}
        for cat in data["categories"]:
            obj, _ = Category.objects.update_or_create(
                name=cat["name"],
                defaults={
                    "is_active": cat.get("is_active", True),
                    "image": cat.get("img", ""),  # Category image support
                },
            )
            category_map[cat["name"]] = obj

        # ---------- ITEMS + SIZES ----------
        for item_data in data["items"]:
            category = category_map[item_data["category"]]

            # Update or create logic taaki image bhi save ho
            item_obj, _ = Item.objects.update_or_create(
                name=item_data["name"],
                category=category,
                defaults={
                    "is_available": True,
                    "image": item_data.get("img", ""),  # Google URL string store hogi
                },
            )

            # Sizes handle karein
            for size_code, price_val in item_data["sizes"].items():
                ItemSize.objects.update_or_create(
                    item=item_obj,
                    size=size_code,
                    defaults={"price": Decimal(price_val)},
                )
