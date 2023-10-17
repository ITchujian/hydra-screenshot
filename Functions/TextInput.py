from PyQt5 import QtGui
from PyQt5.QtWidgets import QTextEdit


class TextInputWidget(QTextEdit):
    """截图区域内的文本输入框"""

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.max_rect = None
        self.main_window = main_window
        self.initUI()

    def initUI(self):
        # 设置背景透明
        palette = self.palette()
        palette.setBrush(QtGui.QPalette.ColorRole.Window, self.main_window.color_transparent)
        self.setPalette(palette)

        # 设置文本颜色和字体
        self.setTextColor(self.main_window.toolbar.current_color())
        self.setCurrentFont(self.main_window.toolbar.current_font())

        self.document().contentsChanged.connect(self.adjustSizeByContent)
        self.adjustSizeByContent()  # 初始化调整高度为一行
        self.hide()

    def adjustSizeByContent(self, margin=30):
        """
        根据文本内容调整高度，限制宽度不超出截图区域，不会出现滚动条
        """
        text_width = self.viewport().width()
        self.document().setTextWidth(text_width)  # 设置文本宽度
        margins = self.contentsMargins()
        height = int(self.document().size().height() + margins.top() + margins.bottom())
        self.setFixedHeight(height)

    def beginNewInput(self, pos, end_pos):
        """
        开始新的文本输入
        """
        self.max_rect = self.main_window.screenArea.normalizeRectF(pos, end_pos)
        self.waitForInput()

    def waitForInput(self):
        """
        等待用户输入
        """
        self.setGeometry(self.max_rect.toRect())  # 设置文本框位置和大小
        self.setFocus()  # 设置焦点
        self.show()

    def loadTextInputBy(self, action):
        """
        载入修改旧的文本
        action: (type, color, font, rect, text)
        """
        self.setTextColor(action[1])  # 设置文本颜色
        self.setCurrentFont(action[2])  # 设置字体
        self.max_rect = action[3]  # 设置文本框位置和大小
        self.append(action[4])  # 添加文本内容
        self.main_window.is_drawing = True
        self.waitForInput()
