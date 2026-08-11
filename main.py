#!/usr/bin/env python3
"""
نرم‌افزار حسابداری آفلاین
برنامه دسکتاپ حسابداری با رابط فارسی RTL
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import run_app

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_app(db_path)
