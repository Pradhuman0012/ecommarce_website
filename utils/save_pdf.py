from pathlib import Path
from django.conf import settings
from io import BytesIO


def save_pdf_once(*, pdf_buffer: BytesIO, filename: str) -> None:
    """
    Saves a PDF to MEDIA_ROOT/bills only once.
    Prevents overwriting existing bills.
    """
    bills_dir = Path(settings.MEDIA_ROOT) / "bills"
    bills_dir.mkdir(parents=True, exist_ok=True)

    file_path = bills_dir / filename

    if not file_path.exists():
        with open(file_path, "wb") as f:
            f.write(pdf_buffer.getvalue())