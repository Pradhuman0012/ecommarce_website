import os
import socket
import subprocess
from datetime import datetime
from pathlib import Path
import platform

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(override=True)

DB_NAME = os.environ.get("PGDATABASE")
DB_USER = os.environ.get("PGUSER")
DB_PASSWORD = os.environ.get("PGPASSWORD")

# 🔒 HARD FIX FOR macOS
DB_HOST = "127.0.0.1"
DB_PORT = "5432"

if platform.system() == "Windows":
    PG_DUMP_BIN = r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"
else:
    PG_DUMP_BIN = "/Library/PostgreSQL/17/bin/pg_dump"

def get_local_ip() -> str:
    """
    Returns the local IPv4 address of the machine.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "unknown_ip"


IP_ADDRESS = get_local_ip()

BACKUP_ROOT = BASE_DIR.parent / "db_backups" / f"{IP_ADDRESS}"


def create_backup() -> None:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
    backup_file = BACKUP_ROOT / f"{timestamp}.dump"

    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    command = [
        PG_DUMP_BIN,
        "-h",
        DB_HOST,
        "-p",
        DB_PORT,
        "-U",
        DB_USER,
        "-F",
        "c",
        "-f",
        str(backup_file),
        DB_NAME,
    ]

    subprocess.run(command, check=True, env=env)


if __name__ == "__main__":
    create_backup()
