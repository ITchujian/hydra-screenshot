from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolBar, QAction

from Settings import Settings


class LongToolBar(QToolBar):
    """长截图区域工具条"""

    def __init__(self, screenshot_area):
        super().__init__()
        self.settings = Settings()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.screenshot_area = screenshot_area
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setStyleSheet("QToolBar {border-radius: 6px;padding: 3px;background-color: #ffffff;}"
                           "QToolBar QToolButton {min-width: 42px;min-height: 42px;}")

        self.normal_style = "QToolBar QToolButton{color: black;}"
        self.selected_style = "QToolBar QToolButton{color: #b35f27;border-radius: 4px;background-color: #f0f0f0}"

        self.save_action = QAction(QIcon(self.settings.get('IconPaths', 'save_icon')), '保存', self)
        self.close_action = QAction(QIcon(self.settings.get('IconPaths', 'cancel_icon')), '关闭', self)
        self.copy_action = QAction(QIcon(self.settings.get('IconPaths', 'ok_icon')), '复制', self)

        self.save_action.triggered.connect(lambda: self.before_save('local'))
        self.close_action.triggered.connect(self.exit)
        self.copy_action.triggered.connect(lambda: self.before_save('clipboard'))

        self.addAction(self.save_action)
        self.addAction(self.close_action)
        self.addAction(self.copy_action)

    def exit(self):
        self.screenshot_area.hide()
        self.hide()

    def before_save(self, target):
        if target == 'local':
            self.screenshot_area.save2Local()
        elif target == 'clipboard':
            self.screenshot_area.save2Clipboard()
        self.exit()

    def enterEvent(self, event):
        self.screenshot_area.setCursor(Qt.CursorShape.ArrowCursor)  # 工具条上显示标准箭头cursor

    def leaveEvent(self, event):
        self.screenshot_area.setCursor(Qt.CursorShape.CrossCursor)  # 十字无箭头
