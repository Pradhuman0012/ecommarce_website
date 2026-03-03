import json

import gspread
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from google.oauth2.service_account import Credentials

from core.decorators import staff_required

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheet():
    creds = Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)
    return client.open_by_key(settings.GOOGLE_SHEET_ID).sheet1


@staff_required
def cms_menu(request):
    sheet = get_sheet()

    # FAST ROW UPDATE (single request)
    if request.method == "POST":
        row = int(request.POST.get("row"))
        values = json.loads(request.POST.get("values"))

        sheet.update(f"A{row}", [values])

        return JsonResponse({"status": "updated"})

    rows = sheet.get_all_values()

    headers = rows[0]
    data = list(enumerate(rows[1:], start=2))

    return render(
        request,
        "cms/menu_cms.html",
        {
            "headers": headers,
            "data": data,
        },
    )
