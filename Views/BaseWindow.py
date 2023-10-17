from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy


class CustomTitleBar(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(60)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.title_label = QLabel(title)
        self.title_label.setObjectName('title')
        self.minimize_button = QPushButton("-")
        self.minimize_button.setObjectName('minimize')
        self.close_button = QPushButton("×")
        self.close_button.setObjectName('close')
        self.setupTitleLabel()
        self.setupEndButton()
        self.setupStyle()
        self.draggable = False  # 默认不可拖动标志

    def setupTitleLabel(self):
        self.layout.addWidget(self.title_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)

    def setupEndButton(self):
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.layout.addItem(spacer)
        self.layout.addWidget(self.minimize_button, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.layout.addWidget(self.close_button, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.minimize_button.clicked.connect(self.parent().showMinimized)
        self.close_button.clicked.connect(self.parent().hide)

    def setupStyle(self):
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
#title {
    font-size: 24px;
    font-weight: bold;
}

#minimize {
    font-size: 20px;
    max-width: 35px;
    min-width: 35px;
    max-height: 35px;
    min-height: 35px;
    color: #f5f5f5;
    background-color: #f5f5f5;
    border-radius: 17px;
}
#minimize:hover, #minimize:pressed {
    background-color: #f2f2f2;
    color: #007aff;
}

#close {
    font-size: 20px;
    max-width: 35px;
    min-width: 35px;
    max-height: 35px;
    min-height: 35px;
    color: #007aff;
    background-color: #007aff;
    border-radius: 17px;
}
#close:hover, #close:pressed {
    background-color: #4c94ff;
    color: #ffffff;
}""")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.draggable = True
            self.drag_position = event.globalPos() - self.parent().frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.draggable:
            if (event.globalPos() - self.drag_position).manhattanLength() > self.parent().dragging_threshold:
                self.parent().move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.draggable = False


class BaseWidget(QWidget):
    def __init__(self, title: str):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle(title)
        self.dragging_threshold = 5  # 鼠标拖动的阈值
        self.title_bar = CustomTitleBar(title, self)
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setContentsMargins(10, 10, 10, 10)
        self.base_layout.addWidget(self.title_bar)
        self.setLayout(self.base_layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(Qt.NoPen)
        rect = self.rect()
        rect.setX(rect.x() + 10)
        rect.setY(rect.y() + 10)
        rect.setWidth(rect.width() - 10)
        painter.drawRoundedRect(rect, 10, 10)
