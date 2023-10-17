from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPen, QFont, QPainter


class Circle:
    number = 0
    __all_circles = []

    def __init__(self, startPoint, color=None, lineWidth=None, radius=None):
        Circle.number += 1
        self.number = Circle.number
        self.startPoint = startPoint
        self.color = color
        self.lineWidth = lineWidth
        self.radius = radius
        Circle.__all_circles.append(self)

    def paint(self, painter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # 反走样
        painter.setPen(QPen(self.color, self.lineWidth))
        painter.setBrush(self.color)

        x, y = self.startPoint.x() - self.radius, self.startPoint.y() - self.radius
        rect = QRectF(x, y, 2 * self.radius, 2 * self.radius)
        painter.drawEllipse(rect)

        font = QFont()
        font.setPointSize(self.lineWidth * 3)
        painter.setFont(font)
        painter.setPen(Qt.white)
        textRect = QRectF(x, y, 2 * self.radius, 2 * self.radius)
        painter.drawText(textRect, Qt.AlignCenter, str(self.number))

    @classmethod
    def destroyAll(cls):
        cls.number = 0
        cls.__all_circles.clear()

    @classmethod
    def getAll(cls):
        return cls.__all_circles

    @classmethod
    def pop(cls):
        return cls.__all_circles.pop()
