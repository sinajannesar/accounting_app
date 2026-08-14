import sys, os, time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow

out_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp_icon_renders')
if not os.path.exists(out_dir):
    os.makedirs(out_dir, exist_ok=True)

app = QApplication([])
app.setAttribute(Qt.AA_UseSoftwareOpenGL)
win = MainWindow()
win.show()
# ensure initial state expanded
win._apply_sidebar_state(False)
app.processEvents()
# take expanded screenshot
pix = win.grab()
pix.save(os.path.join(out_dir, 'mainwindow_expanded.png'))
print('saved expanded')
# collapse and let animation run
win._toggle_sidebar(True)
for _ in range(6):
    app.processEvents()
    time.sleep(0.05)
# finalize
pix2 = win.grab()
pix2.save(os.path.join(out_dir, 'mainwindow_collapsed.png'))
print('saved collapsed')
win.close()
app.quit()
