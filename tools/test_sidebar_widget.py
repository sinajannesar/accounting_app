import sys, os, time
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QPushButton, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt

# import stylesheet from ui.styles
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.styles import APP_STYLE

out_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp_icon_renders')
if not os.path.exists(out_dir):
    os.makedirs(out_dir, exist_ok=True)

app = QApplication([])
app.setStyleSheet(APP_STYLE)

# build a simple window with the sidebar on the right
win = QWidget()
win.setLayoutDirection(Qt.LeftToRight)
layout = QHBoxLayout(win)
layout.setContentsMargins(0,0,0,0)

# Right sidebar frame
sidebar = QFrame()
sidebar.setObjectName('rightSidebar')
sidebar.setLayoutDirection(Qt.RightToLeft)
side_layout = QVBoxLayout(sidebar)
side_layout.setContentsMargins(8,8,8,8)

# helper functions

def add_section_label(text):
    lbl = QPushButton(text)
    lbl.setObjectName('sidebarSection')
    lbl.setEnabled(False)
    lbl.setLayoutDirection(Qt.RightToLeft)
    side_layout.addWidget(lbl)
    return lbl

def add_nav_item(text, key):
    btn = QPushButton(text)
    btn.setObjectName('sidebarItem')
    btn.setCheckable(True)
    btn.setProperty('navKey', key)
    btn.setProperty('fullText', text)
    btn.setLayoutDirection(Qt.RightToLeft)
    side_layout.addWidget(btn)
    return btn

# populate
add_nav_item('داشبورد','dashboard')
add_section_label('عملیات')
add_nav_item('اسناد حسابداری','journal')
add_nav_item('صندوق','cash')
add_section_label('گزارش‌ها')
add_nav_item('تراز آزمایشی','trial')
side_layout.addStretch()

layout.addWidget(QWidget(),1)
layout.addWidget(sidebar)

win.resize(1000,600)
win.show()
app.processEvents()

# capture expanded
pix = win.grab()
pix.save(os.path.join(out_dir,'sidebar_only_expanded.png'))
print('saved expanded')

# set collapsed property and re-polish
sidebar.setProperty('collapsed','true')
sidebar.style().unpolish(sidebar)
sidebar.style().polish(sidebar)
app.processEvents()

pix2 = win.grab()
pix2.save(os.path.join(out_dir,'sidebar_only_collapsed.png'))
print('saved collapsed')

# also check a centered button rendering by collapsing labels programmatically
for btn in sidebar.findChildren(QPushButton):
    if btn.property('navKey'):
        btn.setText('')
        btn.setToolTip(btn.property('fullText'))

app.processEvents()
pix3 = win.grab()
pix3.save(os.path.join(out_dir,'sidebar_only_collapsed_icons.png'))
print('saved collapsed icons')

win.close()
app.quit()
