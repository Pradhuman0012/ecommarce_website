from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from home.utils.menu_loader import load_menu_from_json


class Command(BaseCommand):
    help = "Load menu data from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            required=True,
            help="Path to menu JSON file",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear unused items before loading",
        )

    def handle(self, *args, **options):
        json_path = Path(options["path"])

        try:
            load_menu_from_json(
                json_path=json_path,
                clear_existing=options["clear"],
            )
        except Exception as exc:
            raise CommandError(str(exc))

        self.stdout.write(self.style.SUCCESS("Menu loaded successfully"))


# python manage.py load_menu --path home/fixtures/menu_data.json
