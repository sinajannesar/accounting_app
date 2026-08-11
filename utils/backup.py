"""پشتیبان‌گیری و بازیابی دیتابیس"""

import shutil
from datetime import datetime
from pathlib import Path


def backup_database(db_path, dest_dir=None):
    db_path = Path(db_path)
    if dest_dir is None:
        dest_dir = db_path.parent / "backups"
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"backup_{timestamp}.db"
    shutil.copy2(db_path, dest)
    return dest


def restore_database(db_manager, src_path):
    db_manager.restore(src_path)
