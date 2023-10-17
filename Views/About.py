import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QLabel

from Settings import Settings
from .BaseWindow import BaseWidget


class AboutView(BaseWidget):
    def __init__(self):
        super().__init__("关于软件")
        self.settings = Settings()
        # 添加Logo图片
        logo_label = QLabel(self)
        pixmap = QPixmap(self.settings.get('SoftwareConfig', 'logo'))
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        self.base_layout.addWidget(logo_label)
        # 添加标题
        title_label = QLabel(f"水螅截图 - v{self.settings.version}", self)
        title_label.setStyleSheet('font-family: YouYuan;font-size: 26px; font-weight: bold;')
        title_label.setAlignment(Qt.AlignCenter)
        self.base_layout.addWidget(title_label)

        notice_label = QLabel()
        notice_label.setText("""
            <h4>&nbsp;&nbsp;&nbsp;&nbsp;Hi~我是作者秦宇，当前处于内测阶段，非作者允许请勿进行 转载|反编译|倒卖等 行为。</h4>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;水螅截图是一款基于PyQt5开发的截图工具，主要用于在Windows下进行简单的线条和图形绘制、编辑和导出。软件的功能分为三层：<strong>第一层是线条和文本设置区域，第二层是图形绘制区域，第三层是编辑和导出区域</strong>。软件提供<strong>生成长图（暗灰色支持不太好）、置于顶层</strong>等功能。
                <br>&nbsp;&nbsp;&nbsp;&nbsp;水螅截图还有很多不足，勉强能够轻松完成日常办公中的截图操作。<br>&nbsp;&nbsp;&nbsp;&nbsp;如果您对该软件有任何建议或反馈，<a href="https://www.cnblogs.com/qinyu6/p/17745386.html">欢迎留言</a>。</p>
        """)
        notice_label.setStyleSheet('margin: 10px 20px;border: none; font-family: YouYuan;font-size: 24px;')
        notice_label.setAlignment(Qt.AlignBaseline)
        notice_label.setOpenExternalLinks(True)
        notice_label.setWordWrap(True)  # 设置文本自动换行
        self.base_layout.addWidget(notice_label)

        # 添加声明和版权信息
        disclaimer_label = QLabel("版权所有 © 2023 秦宇")
        disclaimer_label.setStyleSheet('margin: 0 0 10px; font-family: YouYuan;font-size: 20px; color: gray;')
        disclaimer_label.setAlignment(Qt.AlignCenter)
        self.base_layout.addWidget(disclaimer_label)


if __name__ == "__main__":
    app = QApplication([])
    dialog = AboutView()
    dialog.show()
    sys.exit(app.exec_())
