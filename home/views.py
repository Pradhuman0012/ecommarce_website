from django.shortcuts import render, get_object_or_404
from .models import Category, Item

def menu_display(request):
    categories = (
        Category.objects
        .filter(is_active=True)
        .prefetch_related("items__sizes")
        .order_by("name")
    )

    return render(request, "menu/menu_display.html", {
        "categories": categories
    })

def home_view(request):
    categories = Category.objects.filter(is_active=True)

    category_id = request.GET.get("category")
    items = None

    if category_id:
        items = Item.objects.filter(
            category_id=category_id,
            is_available=True
        )

    return render(request, "home/index.html", {
        "categories": categories,
        "items": items,
        "selected_category": int(category_id) if category_id else None,
    })


def category_items(request, pk):
    category = get_object_or_404(Category, pk=pk, is_active=True)
    items = category.items.filter(is_available=True)

    return render(request, "home/shop.html", {
        "category": category,
        "items": items,
    })


def search_items(request):
    query = request.GET.get("q", "")

    items = []
    if query:
        items = Item.objects.filter(
            name__icontains=query,
            is_available=True
        )

    return render(request, "home/search.html", {
        "query": query,
        "items": items,
    })


def about_view(request):
    return render(request, "About.html")