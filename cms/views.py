import json
from typing import List

import gspread
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from google.oauth2.service_account import Credentials

from cms.services.menu_sync import sync_menu_from_sheet
from core.decorators import staff_required

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheet() -> gspread.Worksheet:
    """
    Authorize Google service account and return first worksheet.
    """
    creds = Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)
    return client.open_by_key(settings.GOOGLE_SHEET_ID).sheet1


@staff_required
def cms_menu(request: HttpRequest) -> HttpResponse:
    """
    Menu CMS view.

    GET:
        Render sheet data.

    POST:
        action=update → update full row
        action=create → append new row
    """

    sheet = get_sheet()

    if request.method == "POST":
        action = request.POST.get("action")

        # -----------------------
        # UPDATE EXISTING ROW
        # -----------------------
        if action == "update":
            try:
                row = int(request.POST.get("row", 0))
                values: List[str] = json.loads(request.POST.get("values", "[]"))

                if row <= 1 or not values:
                    return JsonResponse(
                        {"error": "Invalid row data"},
                        status=400,
                    )

                # Update entire row starting from column A
                sheet.update(f"A{row}", [values])

                sync_menu_from_sheet()

                return JsonResponse({"status": "updated"})

            except (ValueError, json.JSONDecodeError):
                return JsonResponse(
                    {"error": "Invalid request payload"},
                    status=400,
                )

        # -----------------------
        # CREATE NEW ENTRY
        # -----------------------
        if action == "create":
            try:
                values: List[str] = json.loads(request.POST.get("values", "[]"))

                if not values:
                    return JsonResponse(
                        {"error": "Empty row cannot be created"},
                        status=400,
                    )

                sheet.append_row(values)

                return JsonResponse({"status": "created"})

            except json.JSONDecodeError:
                return JsonResponse(
                    {"error": "Invalid JSON payload"},
                    status=400,
                )

        return JsonResponse({"error": "Invalid action"}, status=400)

    # -----------------------
    # GET SHEET DATA
    # -----------------------
    rows = sheet.get_all_values()

    if not rows:
        return render(
            request,
            "cms/menu_cms.html",
            {
                "headers": [],
                "data": [],
            },
        )

    headers = rows[0]
    data = list(enumerate(rows[1:], start=2)) if len(rows) > 1 else []

    return render(
        request,
        "cms/menu_cms.html",
        {
            "headers": headers,
            "data": data,
        },
    )
