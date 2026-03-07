from decimal import Decimal

from cms.services.sheet_editor import get_all_rows
from home.models import Category, Item, ItemSize


def normalize_category(value: str) -> str:
    return value.replace("_", " ").title()


def sync_menu_from_sheet():
    rows = get_all_rows()

    for row in rows:

        row = {k.lower(): v for k, v in row.items()}

        category_name = normalize_category(row["category"])
        item_name = row["item name"].strip()

        size = row["price label"].upper()
        price = Decimal(str(row["current price"]))

        image = row.get("image url", "")

        category, _ = Category.objects.get_or_create(name=category_name)

        if not category.image and image:
            category.image = image
            category.save(update_fields=["image"])

        item = Item.objects.filter(name=item_name).first()

        if not item:
            item = Item.objects.create(
                name=item_name,
                category=category,
                image=image,
                is_available=True,
            )
        else:
            item.category = category

            if image:
                item.image = image

            item.save(update_fields=["category", "image"])

        ItemSize.objects.update_or_create(
            item=item,
            size=size,
            defaults={"price": price},
        )
