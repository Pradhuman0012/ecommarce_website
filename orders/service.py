from .models import Order, Recipe, RecipeItem


def generate_recipes_for_order(order: Order, items=None):

    if items is None:
        items = order.items.select_related("item")

    station_map: dict[str, list] = {}

    for order_item in items.select_related("item"):
        station = order_item.item.station
        station_map.setdefault(station, []).append(order_item)

    created_recipes = []

    for station, station_items in station_map.items():

        recipe, _ = Recipe.objects.get_or_create(
            order=order,
            station=station,
        )

        RecipeItem.objects.bulk_create(
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

        created_recipes.append(recipe)

    return created_recipes
