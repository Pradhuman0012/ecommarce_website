import json
from decimal import Decimal
from pathlib import Path

from django.db.models import Count

from home.models import Category, Item, ItemSize


def load_menu_from_json(json_path, clear_existing=False):
    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"{json_path} not found")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if clear_existing:
        # ❗ Delete only items NOT used in any bill
        unused_items = Item.objects.annotate(bill_count=Count("billitem")).filter(
            bill_count=0
        )

        ItemSize.objects.filter(item__in=unused_items).delete()
        unused_items.delete()

        # Categories only if empty
        Category.objects.annotate(item_count=Count("items")).filter(
            item_count=0
        ).delete()

    # ---------- CATEGORIES ----------
    category_map = {}
    for cat in data["categories"]:
        obj, _ = Category.objects.get_or_create(
            name=cat["name"], defaults={"is_active": cat.get("is_active", True)}
        )
        category_map[cat["name"]] = obj

    # ---------- ITEMS + SIZES ----------
    for item in data["items"]:
        category = category_map[item["category"]]

        item_obj, _ = Item.objects.get_or_create(
            name=item["name"], category=category, defaults={"is_available": True}
        )

        for size, price in item["sizes"].items():
            ItemSize.objects.update_or_create(
                item=item_obj, size=size, defaults={"price": Decimal(price)}
            )

    print("✅ Menu loaded safely (used items preserved)")
