from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtWidgets import QAction, QColorDialog


class ColorAction(QAction):
    """
    颜色选择器
    参数：
    - text: 图标上显示的文本
    - parent: 父部件
    """

    def __init__(self, text, color=None, parent=None):
        super().__init__(text, parent)
        self.curColor = color or Qt.GlobalColor.red  # 当前颜色
        self.pixmap = QPixmap(32, 32)  # 图片对象，用于显示颜色图标
        self.refresh(self.curColor)
        self.triggered.connect(self.onTriggered)

    def refresh(self, color):
        """
        刷新颜色
        参数：
        - color: 颜色值
        """
        self.curColor = color  # 更新当前颜色
        self.pixmap.fill(color)  # 填充图片对象为指定颜色
        self.setIcon(QIcon(self.pixmap))  # 设置图标为图片对象
        self.parent().thin_line.refresh(color)  # 刷新小尺寸行动条颜色
        self.parent().medium_line.refresh(color)  # 刷新中等尺寸行动条颜色
        self.parent().thick_line.refresh(color)  # 刷新大尺寸行动条颜色

    def onTriggered(self):
        """
        触发事件处理函数
        """
        col = QColorDialog.getColor(self.curColor, self.parent(), title='选择颜色')  # 弹出颜色选择对话框
        if col.isValid():
            self.refresh(QColor(col))  # 更新当前颜色为所选颜色
            self.parent().screenshot_area.textInputWg.setTextColor(col)  # 设置文本输入窗口文本颜色
