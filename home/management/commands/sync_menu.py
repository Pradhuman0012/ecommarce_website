from django.core.management.base import BaseCommand
from django.db import transaction

from cms.services.menu_sync import sync_menu_from_sheet


class Command(BaseCommand):
    help = "Sync menu from Google Sheet"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        sync_menu_from_sheet()
        self.stdout.write(self.style.SUCCESS("Menu synced"))
