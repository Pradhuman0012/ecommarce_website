import csv
import io
from typing import Any, Dict

import requests


class GoogleMenuServiceError(Exception):
    """Raised when Google Sheet fetch fails."""

    pass


def fetch_google_menu() -> Dict[str, Any]:
    """
    Fetch and transform Google Sheet CSV into structured dictionary.
    """

    CSV_URL = (
        "https://docs.google.com/spreadsheets/d/e/"
        "2PACX-1vQWGG0hgrRrDuRFn4729qiS-iTLG-CD4R6fC9HwfiTZxbmiBnVtyzPB_HyoW1jxuDO5_0orKp07j_27/pub?gid=0&single=true&output=csv"
    )

    try:
        response = requests.get(CSV_URL, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise GoogleMenuServiceError("Failed to fetch Google Sheet") from exc

    decoded = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    formatted: Dict[str, Any] = {}

    for row in reader:
        category_key = row["Category"]
        if not category_key:
            continue

        if category_key not in formatted:
            formatted[category_key] = {
                "title": row["Title"],
                "type": row["Type"],
                "image": row["Image URL"],
                "items": {},
            }

        item_name = row["Item Name"]

        if item_name not in formatted[category_key]["items"]:
            formatted[category_key]["items"][item_name] = {
                "image": row["Image URL"],
                "prices": {},
            }

        formatted[category_key]["items"][item_name]["prices"][row["Price Label"]] = {
            "current_price": float(row["Current Price"] or 0),
            "original_price": float(row["Original Price (Strike)"] or 0),
        }

    return formatted
