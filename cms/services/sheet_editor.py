import gspread
from django.conf import settings
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheet():
    creds = Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)

    sheet = client.open_by_key("1AMBuQTciSFwU7Ev3hPvmFCSQaQJh5bYDxPf2yZZnvVU")

    return sheet.sheet1


def get_all_rows():
    sheet = get_sheet()
    return sheet.get_all_records()


def update_cell(row, col, value):
    sheet = get_sheet()
    sheet.update_cell(row, col, value)


def append_row(data):
    sheet = get_sheet()
    sheet.append_row(data)
