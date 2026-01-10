from .models import Order, Recipe, RecipeItem


def generate_recipes_for_order(order: Order) -> None:
    """
    Create Kitchen and Barista recipes based on ordered items.
    """

    station_map: dict[str, list] = {}

    for order_item in order.items.select_related("item"):
        station = order_item.item.station
        station_map.setdefault(station, []).append(order_item)

    for station, items in station_map.items():
        recipe = Recipe.objects.create(
            order=order,
            station=station,
        )

        RecipeItem.objects.bulk_create(
            [
                RecipeItem(
                    recipe=recipe,
                    item_name=oi.item.name,
                    quantity=oi.quantity,
                    priority=oi.priority,
                    notes=oi.notes,
                )
                for oi in items
            ]
        )
