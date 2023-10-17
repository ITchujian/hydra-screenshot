import sys

import keyboard
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QRect, QPoint, QSize
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QClipboard
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QWidget, QGraphicsDropShadowEffect

from Settings import Settings
from .ScreenArea import ScreenShotWidget
from .SettingView import SettingWindow
from .About import AboutView


class StickyNoteWidget(QWidget):
    update_top_info = pyqtSignal(QPoint, float)

    def __init__(self, pixmap: QPixmap, coordinate: QPoint, scale_factor: float, parent=None):
        super().__init__(parent)
        self.settings = Settings()
        self.setWindowTitle('贴图置顶')
        self.setWindowIcon(QIcon(self.settings.get('SoftwareConfig', 'exe_icon')))
        self.setWindowFlags(Qt.ToolTip | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.pixmap = pixmap
        self.coordinate = coordinate
        self.original_pixmap = pixmap
        self.scale_factor = scale_factor
        self.copy_action = QAction(QIcon(self.settings.get('IconPaths', 'copy_icon')), "复制", None)
        self.destroy_action = QAction(QIcon(self.settings.get('IconPaths', 'close_icon')), "关闭", None)
        self.copy_action.triggered.connect(self.copyPixmap2Clipboard)
        self.destroy_action.triggered.connect(self.hide)
        self.drag_position = None
        # 调整控件大小，保证它和 pixmap 大小一致
        self.width_ratio = pixmap.width() / pixmap.height()
        self.setGeometry(self.coordinate.x(), self.coordinate.y(),
                         int(pixmap.width() * scale_factor) + 8, int(pixmap.height() * scale_factor) + 8)
        # 创建阴影效果
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setOffset(0, 0)  # 调整阴影偏移量
        self.shadow.setBlurRadius(6)  # 调整阴影半径
        self.shadow.setColor(QColor(179, 95, 39))  # 调整阴影颜色
        self.setGraphicsEffect(self.shadow)

    def wheelEvent(self, event):
        angle_delta = event.angleDelta().y()
        # 向上滚动，放大控件和图片
        if angle_delta > 1:
            self.scale_factor *= 1.1
        # 向下滚动，缩小控件和图片
        elif angle_delta < -1:
            self.scale_factor *= 0.9
        # 根据缩放因子重新设置控件大小和图片
        new_width = int(self.original_pixmap.width() * self.scale_factor)
        new_height = int(self.original_pixmap.height() * self.scale_factor)
        self.setFixedSize(new_width + 8, new_height + 8)
        self.pixmap = self.original_pixmap.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
        self.update()
        self.update_top_info.emit(self.coordinate, self.scale_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.coordinate = QPoint(self.geometry().x(), self.geometry().y())
            self.update_top_info.emit(self.coordinate, self.scale_factor)
            self.drag_position = None

    def setPixmap(self, pixmap: QPixmap, coordinate: QPoint):
        self.pixmap = pixmap
        self.original_pixmap = pixmap
        self.width_ratio = pixmap.width() / pixmap.height()
        self.setGeometry(coordinate.x(), coordinate.y(), pixmap.width() + 8, pixmap.height() + 8)
        self.scale_factor = 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pixmap_rect = QRect(QPoint(4, 4), QSize(self.width() - 8, int((self.width() - 8) / self.width_ratio)))
        painter.drawPixmap(pixmap_rect, self.pixmap)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(self.copy_action)
        menu.addAction(self.destroy_action)
        menu.exec_(event.globalPos())

    def copyPixmap2Clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(self.pixmap, mode=QClipboard.Clipboard)


class TrayProgram(QObject):
    startScreenshotSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon(self.settings.get('SoftwareConfig', 'exe_icon')))
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setToolTip('水螅截图\nHydra-Screenshot')
        self.tray_icon.setIcon(QIcon(self.settings.get('SoftwareConfig', 'exe_icon')))
        self.screenShotWg = ScreenShotWidget()
        self.screenShotWg.send_pixmap_signal.connect(self.show_top)
        self.startScreenshotSignal.connect(self.screenShotWg.start)
        self.pixmap = None
        self.coordinate = None
        self.scale_factor = 1.0
        # 实现一个无边框且置顶的弹出窗口menu
        self.menu = QMenu()
        self.menu.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.menu.setAttribute(Qt.WA_TranslucentBackground)  # 设置半透明背景
        self.settings_action = QAction("软件设置")
        self.show_top_action = QAction("显示贴图")
        self.about_action = QAction("关于")
        self.exit_action = QAction("退出")
        self.settings_action.triggered.connect(self.show_settings)
        self.show_top_action.triggered.connect(lambda: self.show_top(self.pixmap, self.coordinate))
        self.about_action.triggered.connect(self.show_about)
        self.exit_action.triggered.connect(self.exit_program)
        self.menu.addAction(self.settings_action)
        self.menu.addAction(self.show_top_action)
        self.menu.addSeparator()
        self.menu.addAction(self.about_action)
        self.menu.addAction(self.exit_action)
        self.tray_icon.setContextMenu(self.menu)
        self.set_menu_style()  # 设置菜单样式
        self.settings_window = SettingWindow(settings=self.settings)
        screenshot_key = self.settings.get('ShortKeySettings', 'screenshot')
        keyboard.add_hotkey(screenshot_key, self.startScreenshotSignal.emit)
        self.about_window = AboutView()

    def set_menu_style(self):
        qss = """
            QMenu {
                background-color: #FFFFFF;
                padding: 4px;
                border-radius: 8px;
            }

            QMenu::item {
                color: #2b3134;
                padding: 6px 24px;
            }

            QMenu::item:selected {
                background-color: #f0f0f0;
                color: #b35f27;
                border-radius: 6px;
            }

            QMenu::item:disabled {
                color: #BBBBBB;
            }

            QMenu::separator {
                height: 1px;
                background-color: #CCCCCC;
                margin: 4px 0px;
            }
        """

        self.menu.setStyleSheet(qss)

    def show_settings(self):
        self.settings_window.show()

    def show_about(self):
        self.about_window.show()

    def exit_program(self):
        keyboard.remove_all_hotkeys()
        sys.exit()

    def show_top(self, pixmap: QPixmap, coordinate: QPoint):
        if pixmap and coordinate:
            self.pixmap = pixmap
            self.coordinate = coordinate
            sticky_note_widget = StickyNoteWidget(pixmap, coordinate, self.scale_factor, parent=self.settings_window)
            sticky_note_widget.update_top_info.connect(self.update_current_top)
            sticky_note_widget.show()

    def update_current_top(self, coordinate: QPoint, scale_factor: float):
        self.coordinate = coordinate
        self.scale_factor = scale_factor

    def run(self):
        self.tray_icon.show()
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    tray_program = TrayProgram()
    tray_program.run()
