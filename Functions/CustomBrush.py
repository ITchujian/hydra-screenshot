from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction


class LineWidthAction(QAction):
    """
    画笔粗细选择器
    参数：
    - text: 图标上显示的文本
    - parent: 父部件
    - lineWidth: 画笔粗细值
    """

    def __init__(self, text, parent, lineWidth):
        super().__init__(text, parent)
        self.lineWidth = lineWidth
        self.refresh(Qt.GlobalColor.red)  # 刷新图标和颜色
        self.triggered.connect(self.onTriggered)
        self.setVisible(False)

    def refresh(self, color):
        """
        刷新图标和颜色
        参数：
        - color: 画笔颜色
        """
        painter = self.parent().screenshot_area.screenArea._painter  # 获取绘图对象
        dotRadius = QPointF(self.lineWidth, self.lineWidth)
        centerPoint = self.parent().icon_pixmap_center()  # 获取图标中心点坐标
        pixmap = self.parent().icon_pixmap_copy()  # 复制图标图片
        painter.begin(pixmap)
        painter.setPen(self.parent().screenshot_area.pen_transparent)  # 设置画笔为透明
        painter.setBrush(color)  # 设置填充颜色
        painter.drawEllipse(QRectF(centerPoint - dotRadius, centerPoint + dotRadius))  # 绘制圆形
        painter.end()
        self.setIcon(QIcon(pixmap))  # 设置图标

    def onTriggered(self):
        """
        触发事件处理函数
        """
        self.parent().set_current_line_width(self.lineWidth)
