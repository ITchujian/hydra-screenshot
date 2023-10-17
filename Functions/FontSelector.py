from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QAction, QFontDialog


class FontAction(QAction):
    """
    字体选择器
    参数：
    - text: 图标上显示的文本
    - parent: 父部件
    """

    def __init__(self, icon, text, parent):
        super().__init__(icon, text, parent)
        # self.setIcon(QIcon("img/sys/font.png"))  # 设置图标
        self.curFont = self.parent().screenshot_area.font_textInput  # 获取当前字体对象
        self.triggered.connect(self.onTriggered)
        self.setVisible(False)

    def onTriggered(self):
        """
        触发事件处理函数
        """
        font, ok = QFontDialog.getFont(self.curFont, self.parent(), caption='选择字体')  # 弹出字体选择对话框
        if ok:
            self.curFont = QFont(font)  # 更新当前字体对象
            self.parent().screenshot_area.textInputWg.setCurrentFont(self.curFont)  # 设置文本输入窗口字体
