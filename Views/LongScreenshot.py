from datetime import datetime
from pathlib import Path
from threading import Thread

import numpy as np
from PIL import ImageGrab
from PyQt5.QtCore import Qt, QRectF, QObject, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QRegion, QImage, QPixmap, QFont
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog
from pynput import mouse

from Functions import merge_images, save_merge_result, get_rgb_image
from Settings import Settings
from .LongToolBar import LongToolBar


class MouseListener(QObject):
    """ 鼠标滚动监听器 """

    scroll_signal = pyqtSignal(int, int, int, int)

    def __init__(self):
        super().__init__()
        # 创建鼠标监听器
        self.listener = mouse.Listener(on_scroll=self.on_scroll)

    def on_scroll(self, x, y, dx, dy):
        """ 监听鼠标滚轮事件 """
        self.scroll_signal.emit(x, y, dx, dy)

    def start(self):
        """ 开始监听 """
        self.listener.start()

    def stop(self):
        """ 停止监听 """
        self.listener.stop()


class LongScreenshot(QWidget):
    fileType_img = '图片文件 (*.jpg *.jpeg *.gif *.png *.bmp)'
    dir_lastAccess = Path.cwd()  # 最后访问目录

    def __init__(self, center_rectf: QRectF):
        super().__init__()
        self.settings = Settings()
        self.setMouseTracking(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint |
                            Qt.ToolTip)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.center_rectf = center_rectf  # 截屏区域
        self.images = []
        self.ml = MouseListener()
        self.ml_thread = Thread(target=self.ml.start)
        self.ml_thread.start()
        # 将信号连接到槽函数
        self.ml.scroll_signal.connect(self.wheelScroll)
        self.toolbar = LongToolBar(self)
        self.getLongScreenshot()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipRegion(QRegion(self.rect()) - QRegion(self.center_rectf.toRect()))
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))
        painter.setClipping(False)
        self.paintText()
        self.paintToolBar()
        self.paintLongScreenshot()

    def paintText(self):
        painter = QPainter(self)
        font = QFont("Arial", 12)
        painter.setPen(QColor(245, 245, 245))
        painter.setFont(font)
        text_rect = QRectF(self.center_rectf.topLeft().x(), self.center_rectf.topLeft().y() - self.toolbar.height(),
                           self.center_rectf.width(), self.toolbar.height())
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.TextWrapAnywhere,
                         "滚动到底后请停下|暗色可能出现bug\n按下ESC键可取消")

    def paintToolBar(self):
        self.toolbar.adjustSize()
        toolbarRectf = QRectF(self.toolbar.rect())
        if (self.rect().height() - self.center_rectf.bottomRight().y()) > toolbarRectf.height():
            toolbarRectf.moveTopRight(self.center_rectf.bottomRight() + QPoint(-5, 5))
        elif self.center_rectf.topRight().y() > toolbarRectf.height():
            toolbarRectf.moveBottomRight(self.center_rectf.topRight() + QPoint(-5, -5))
        else:
            toolbarRectf.moveBottomRight(self.center_rectf.bottomRight() + QPoint(-5, -5))
        if toolbarRectf.x() < 0:
            pos = toolbarRectf.topLeft()
            pos.setX(self.center_rectf.x() + 5)
            toolbarRectf.moveTo(pos)
        self.toolbar.move(toolbarRectf.topLeft().toPoint())
        self.toolbar.show()

    def paintLongScreenshot(self):
        painter = QPainter(self)
        image_rgb = get_rgb_image(self.images[-1])
        # 获取图像的尺寸信息
        height, width, channel = image_rgb.shape
        preview_image = QImage(image_rgb.data, width, height, width * channel, QImage.Format_RGB888)
        ratio = self.images[-1].shape[1] / self.images[-1].shape[0]
        rect_width = (self.rect().width() - self.center_rectf.width()) / 2
        rect_height = int(rect_width / ratio)
        if (self.rect().width() - self.center_rectf.bottomRight().x()) > rect_width + 5:
            x = self.center_rectf.topRight().x() + 5
        else:
            x = self.center_rectf.topLeft().x() - rect_width - 5
        y = ((self.center_rectf.topRight().y() + self.center_rectf.bottomRight().y()) / 2) - rect_height / 2
        preview_rect = QRectF(x, y, rect_width, rect_height)
        painter.drawImage(preview_rect, preview_image)

    def mousePressEvent(self, event) -> None:
        self.toolbar.raise_()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.images.clear()

    def wheelScroll(self, x, y, dx, dy):
        if self.center_rectf.contains(x, y):
            if dy < 0:
                self.getLongScreenshot()
                self.update()

    def grabCenter(self):
        temp = ImageGrab.grab(bbox=self.center_rectf.getCoords())
        self.images.append(np.array(temp))

    def getLongScreenshot(self):
        self.grabCenter()
        self.images[-1] = merge_images(self.images)
        if len(self.images) == 2:
            self.images.pop(0)
        return self.images[-1]

    def save2Clipboard(self):
        """将截图区域复制到剪贴板"""
        image = self.getLongScreenshot()
        # 将图像从BGR格式转换为RGB格式
        image_rgb = get_rgb_image(image)
        # 获取图像的尺寸信息
        height, width, channel = image_rgb.shape
        # 创建QImage对象
        qimage = QImage(image_rgb.data, width, height, width * channel, QImage.Format_RGB888)
        QApplication.clipboard().setPixmap(QPixmap.fromImage(qimage))

    def save2Local(self):
        """保存截图到本地"""
        self.settings = Settings()
        # 获取截图
        image = self.getLongScreenshot()
        # 处理默认文件名
        defaultFileName = self.get_default_filename()
        if self.settings.get('SaveSettings', 'is_silent_save') == 'True':
            fileFolder = Path(self.settings.get('SaveSettings', 'default_path_edit'))
            module = self.settings.get('SaveSettings', 'save_name_edit')
            fileName = self.sys_getCurTime(self.settings.module_parser(module))
            filePath = str(fileFolder / fileName)
        else:
            filePath, _ = QFileDialog.getSaveFileName(self, "保存文件",
                                                      str(LongScreenshot.dir_lastAccess / defaultFileName),
                                                      LongScreenshot.fileType_img)
        if filePath:
            # 更新最后访问目录
            LongScreenshot.dir_lastAccess = Path(filePath).parent
            selectedFilePath = Path(filePath)
            selectedFilePath = self.handle_existing_filepath(selectedFilePath)
            # 保存图像
            save_merge_result(str(selectedFilePath), image)

    def get_default_filename(self):
        """根据不同条件生成默认文件名"""
        # 这里可以根据需求定义不同的默认文件名逻辑
        curTime = self.sys_getCurTime('%Y%m%d_%H%M%S')
        return f"hydra_{curTime}.png"

    def handle_existing_filepath(self, filePath):
        """处理已存在的文件路径"""
        # 如果文件已经存在，可以根据需求进行自动化处理，比如添加序号、修改文件名等
        idx = 1
        baseName, ext = filePath.stem, filePath.suffix
        while filePath.exists():
            filePath = filePath.with_stem(f"{baseName}_{idx}")
            idx += 1
        return filePath

    def sys_getCurTime(self, fmt='%Y-%m-%d %H:%M:%S'):
        """获取字符串格式的当前时间"""
        return datetime.now().strftime(fmt)
