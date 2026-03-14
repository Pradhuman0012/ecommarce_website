from .models import Recipe, RecipeItem


def generate_recipes_for_order(order, items):
    """
    Generate recipes only for provided order items.
    """

    station_map = {}

    for oi in items:
        station = oi.item.station
        station_map.setdefault(station, []).append(oi)

    recipes_with_items = []

    for station, station_items in station_map.items():

        recipe, _ = Recipe.objects.get_or_create(
            order=order,
            station=station,
        )

        new_items = RecipeItem.objects.bulk_create(
            [
                RecipeItem(
                    recipe=recipe,
                    item_name=oi.item.name,
                    quantity=oi.quantity,
                    size=oi.size,
                    priority=oi.priority,
                    notes=oi.notes,
                )
                for oi in station_items
            ]
        )

        recipes_with_items.append((recipe, new_items))

    return recipes_with_items
