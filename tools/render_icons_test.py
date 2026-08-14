from PyQt5.QtGui import QPixmap, QPainter, QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
import sys, os

icons_dir = os.path.join(os.path.dirname(__file__), '..', 'ui', 'icons')
out_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp_icon_renders')
os.makedirs(out_dir, exist_ok=True)

files = [f for f in os.listdir(icons_dir) if f.lower().endswith('.svg')]
if not files:
    print('no svgs found')
    sys.exit(1)

app = QApplication([])

for name in files:
    path = os.path.join(icons_dir, name)
    for size in (24, 64):
        try:
            ic = QIcon(path)
            pix = ic.pixmap(size, size)
            if pix.isNull():
                print('QIcon produced null pixmap for', path)
                continue
            out = os.path.join(out_dir, f"{name}.{size}px.png")
            pix.save(out)
            print('rendered', out)
        except Exception as e:
            print('error rendering', path, e)

print('done')
