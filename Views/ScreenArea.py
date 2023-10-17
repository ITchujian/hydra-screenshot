import math
import os
from pathlib import Path
from datetime import datetime

from PyQt5.QtCore import QRectF, QRect, QSizeF, QPoint, QMarginsF, QObject, QMimeData, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QCursor, QRgba64, QTextOption, QPainterPath, QKeySequence
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog

from Functions import TextInputWidget, Circle
from .ToolBar import *


class ScreenArea(QObject):
    """屏幕区域（提供各种算法的核心类），划分为9个子区域：
    TopLeft，Top，TopRight
    Left，Center，Right
    BottomLeft，Bottom，BottomRight
    其中Center根据start、end两个QPointF确定
    """

    def __init__(self, screenshot_area):
        super().__init__()
        self.screenshot_area = screenshot_area
        self._pt_start = QPointF()  # 划定截图区域时鼠标左键按下的位置（topLeft）
        self._pt_end = QPointF()  # 划定截图区域时鼠标左键松开的位置（bottomRight）
        self._rt_toolbar = QRectF()  # 工具条的矩形
        self._actions = []  # 在截图区域上的所有编辑行为（矩形、椭圆、涂鸦、文本输入等）
        self._pt_startEdit = QPointF()  # 在截图区域上绘制矩形、椭圆时鼠标左键按下的位置（topLeft）
        self._pt_endEdit = QPointF()  # 在截图区域上绘制矩形、椭圆时鼠标左键松开的位置（bottomRight）
        self._pointfs = []  # 涂鸦经过的所有点
        self._painter = QPainter()  # 独立于ScreenShotWidget之外的画家类
        self._textOption = QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._textOption.setWrapMode(QTextOption.WrapMode.WrapAnywhere)  # 文本在矩形内自动换行
        self.captureScreen()

    def captureScreen(self):
        """抓取整个屏幕的截图"""
        # screen = QGuiApplication.primaryScreen()
        self._screenPixmap = QApplication.primaryScreen().grabWindow(0)
        self._pixelRatio = self._screenPixmap.devicePixelRatio()  # 设备像素比
        self._rt_screen = self.screenLogicalRectF()
        self.remakeNightArea()

    def normalizeRectF(self, topLeftPoint, bottomRightPoint):
        """根据起止点生成宽高非负数的QRectF，通常用于bottomRightPoint比topLeftPoint更左更上的情况
        入参可以是QPoint或QPointF"""
        rectf = QRectF(topLeftPoint, bottomRightPoint)
        x = rectf.x()
        y = rectf.y()
        w = rectf.width()
        h = rectf.height()
        if w < 0:  # bottomRightPoint在topLeftPoint左侧时，topLeftPoint往左移动
            x = x + w
            w = -w
        if h < 0:  # bottomRightPoint在topLeftPoint上侧时，topLeftPoint往上移动
            y = y + h
            h = -h
        return QRectF(x, y, w, h)

    def physicalRectF(self, rectf):
        """计算划定的截图区域的（缩放倍率1.0的）原始矩形（会变大）
        rectf：划定的截图区域的矩形。可为QRect或QRectF"""
        return QRectF(rectf.x() * self._pixelRatio, rectf.y() * self._pixelRatio,
                      rectf.width() * self._pixelRatio, rectf.height() * self._pixelRatio)

    def logicalRectF(self, physicalRectF):
        """根据原始矩形计算缩放后的矩形（会变小）
        physicalRectF：缩放倍率1.0的原始矩形。可为QRect或QRectF"""
        return QRectF(physicalRectF.x() / self._pixelRatio, physicalRectF.y() / self._pixelRatio,
                      physicalRectF.width() / self._pixelRatio, physicalRectF.height() / self._pixelRatio)

    def physicalPixmap(self, rectf, editAction=False):
        """根据指定区域获取其原始大小的（缩放倍率1.0的）QPixmap
        rectf：指定区域。可为QRect或QRectF
        editAction:是否带上编辑结果"""
        if editAction:
            canvasPixmap = self.screenPhysicalPixmapCopy()
            self._painter.begin(canvasPixmap)
            self.paintEachEditAction(self._painter, textBorder=False)
            self._painter.end()
            return canvasPixmap.copy(self.physicalRectF(rectf).toRect())
        else:
            return self._screenPixmap.copy(self.physicalRectF(rectf).toRect())

    def screenPhysicalRectF(self):
        return QRectF(self._screenPixmap.rect())

    def screenLogicalRectF(self):
        return QRectF(QPointF(0, 0), self.screenLogicalSizeF())  # 即当前屏幕显示的大小

    def screenPhysicalSizeF(self):
        return QSizeF(self._screenPixmap.size())

    def screenLogicalSizeF(self):
        return QSizeF(self._screenPixmap.width() / self._pixelRatio, self._screenPixmap.height() / self._pixelRatio)

    def screenPhysicalPixmapCopy(self):
        return self._screenPixmap.copy()

    def screenLogicalPixmapCopy(self):
        return self._screenPixmap.scaled(self.screenLogicalSizeF().toSize())

    def centerPhysicalRectF(self):
        return self.physicalRectF(self._rt_center)

    def centerLogicalRectF(self):
        """根据屏幕上的start、end两个QPointF确定"""
        return self._rt_center

    def centerPhysicalPixmap(self, editAction=True):
        """截图区域的QPixmap
        editAction:是否带上编辑结果"""
        return self.physicalPixmap(self._rt_center + QMarginsF(-1, -1, 1, 1), editAction=editAction)

    def centerTopMid(self):
        return self._pt_centerTopMid

    def centerBottomMid(self):
        return self._pt_centerBottomMid

    def centerLeftMid(self):
        return self._pt_centerLeftMid

    def centerRightMid(self):
        return self._pt_centerRightMid

    def setStartPoint(self, pointf, remake=False):
        self._pt_start = pointf
        if remake:
            self.remakeNightArea()

    def setEndPoint(self, pointf, remake=False):
        self._pt_end = pointf
        if remake:
            self.remakeNightArea()

    def setCenterArea(self, start, end):
        self._pt_start = start
        self._pt_end = end
        self.remakeNightArea()

    def remakeNightArea(self):
        """重新划分九宫格区域。根据中央截图区域计算出来的其他8个区域、截图区域四个边框中点坐标等都是logical的"""
        self._rt_center = self.normalizeRectF(self._pt_start, self._pt_end)
        # 中央区域上下左右边框的中点，用于调整大小
        self._pt_centerTopMid = (self._rt_center.topLeft() + self._rt_center.topRight()) / 2
        self._pt_centerBottomMid = (self._rt_center.bottomLeft() + self._rt_center.bottomRight()) / 2
        self._pt_centerLeftMid = (self._rt_center.topLeft() + self._rt_center.bottomLeft()) / 2
        self._pt_centerRightMid = (self._rt_center.topRight() + self._rt_center.bottomRight()) / 2
        # 以截图区域左上、上中、右上、左中、右中、左下、下中、右下为中心的正方形区域，用于调整大小
        self._square_topLeft = self.squareAreaByCenter(self._rt_center.topLeft())
        self._square_topRight = self.squareAreaByCenter(self._rt_center.topRight())
        self._square_bottomLeft = self.squareAreaByCenter(self._rt_center.bottomLeft())
        self._square_bottomRight = self.squareAreaByCenter(self._rt_center.bottomRight())
        self._square_topMid = self.squareAreaByCenter(self._pt_centerTopMid)
        self._square_bottomMid = self.squareAreaByCenter(self._pt_centerBottomMid)
        self._square_leftMid = self.squareAreaByCenter(self._pt_centerLeftMid)
        self._square_rightMid = self.squareAreaByCenter(self._pt_centerRightMid)
        # 除中央截图区域外的8个区域
        self._rt_topLeft = QRectF(self._rt_screen.topLeft(), self._rt_center.topLeft())
        self._rt_top = QRectF(QPointF(self._rt_center.topLeft().x(), 0), self._rt_center.topRight())
        self._rt_topRight = QRectF(QPointF(self._rt_center.topRight().x(), 0),
                                   QPointF(self._rt_screen.width(), self._rt_center.topRight().y()))
        self._rt_left = QRectF(QPointF(0, self._rt_center.topLeft().y()), self._rt_center.bottomLeft())
        self._rt_right = QRectF(self._rt_center.topRight(),
                                QPointF(self._rt_screen.width(), self._rt_center.bottomRight().y()))
        self._rt_bottomLeft = QRectF(QPointF(0, self._rt_center.bottomLeft().y()),
                                     QPointF(self._rt_center.bottomLeft().x(), self._rt_screen.height()))
        self._rt_bottom = QRectF(self._rt_center.bottomLeft(),
                                 QPointF(self._rt_center.bottomRight().x(), self._rt_screen.height()))
        self._rt_bottomRight = QRectF(self._rt_center.bottomRight(), self._rt_screen.bottomRight())

    def squareAreaByCenter(self, pointf):
        """以QPointF为中心的正方形QRectF"""
        rectf = QRectF(0, 0, 15, 15)
        rectf.moveCenter(pointf)
        return rectf

    def aroundAreaWithoutIntersection(self):
        """中央区域周边的4个方向的区域（无交集）
        上区域(左上、上、右上)：0, 0, maxX, topRight.y
        下区域(左下、下、右下)：0, bottomLeft.y, maxX, maxY-bottomLeft.y
        左区域(左)：0, topRight.y, bottomLeft.x-1, center.height
        右区域(右)：topRight.x+1, topRight.y, maxX - topRight.x, center.height"""
        screenSizeF = self.screenLogicalSizeF()
        pt_topRight = self._rt_center.topRight()
        pt_bottomLeft = self._rt_center.bottomLeft()
        centerHeight = pt_bottomLeft.y() - pt_topRight.y()
        return [QRectF(0, 0, screenSizeF.width(), pt_topRight.y()),
                QRectF(0, pt_bottomLeft.y(), screenSizeF.width(), screenSizeF.height() - pt_bottomLeft.y()),
                QRectF(0, pt_topRight.y(), pt_bottomLeft.x() - 1, centerHeight),
                QRectF(pt_topRight.x() + 1, pt_topRight.y(), screenSizeF.width() - pt_topRight.x(), centerHeight)]

    def setBeginDragPoint(self, pointf):
        """计算开始拖拽位置距离截图区域左上角的向量"""
        self._drag_vector = pointf - self._rt_center.topLeft()

    def getNewPosAfterDrag(self, pointf):
        """计算拖拽后截图区域左上角的新位置"""
        return pointf - self._drag_vector

    def moveCenterAreaTo(self, pointf):
        """限制拖拽不能超出屏幕范围"""
        self._rt_center.moveTo(self.getNewPosAfterDrag(pointf))
        startPointF = self._rt_center.topLeft()
        if startPointF.x() < 0:
            self._rt_center.moveTo(0, startPointF.y())
            startPointF = self._rt_center.topLeft()
        if startPointF.y() < 0:
            self._rt_center.moveTo(startPointF.x(), 0)
        screenSizeF = self.screenLogicalSizeF()
        endPointF = self._rt_center.bottomRight()
        if endPointF.x() > screenSizeF.width():
            self._rt_center.moveBottomRight(QPointF(screenSizeF.width(), endPointF.y()))
            endPointF = self._rt_center.bottomRight()
        if endPointF.y() > screenSizeF.height():
            self._rt_center.moveBottomRight(QPointF(endPointF.x(), screenSizeF.height()))
        self.setCenterArea(self._rt_center.topLeft(), self._rt_center.bottomRight())

    def setBeginAdjustPoint(self, pointf):
        """判断开始调整截图区域大小时鼠标左键在哪个区（不可能是中央区域），用于判断调整大小的意图方向"""
        self._mousePos = self.getMousePosBy(pointf)

    def getMousePosBy(self, pointf):
        if self._square_topLeft.contains(pointf):
            return 'TL'
        elif self._square_topMid.contains(pointf):
            return 'T'
        elif self._square_topRight.contains(pointf):
            return 'TR'
        elif self._square_leftMid.contains(pointf):
            return 'L'
        elif self._rt_center.contains(pointf):
            return 'CENTER'
        elif self._square_rightMid.contains(pointf):
            return 'R'
        elif self._square_bottomLeft.contains(pointf):
            return 'BL'
        elif self._square_bottomMid.contains(pointf):
            return 'B'
        elif self._square_bottomRight.contains(pointf):
            return 'BR'
        else:
            return 'ERROR'

    def adjustCenterAreaBy(self, pointf):
        """根据开始调整截图区域大小时鼠标左键在哪个区（不可能是中央区域），判断调整大小的意图方向，判定新的开始、结束位置"""
        startPointF = self._rt_center.topLeft()
        endPointF = self._rt_center.bottomRight()
        if self._mousePos == 'TL':
            startPointF = pointf
        elif self._mousePos == 'T':
            startPointF = QPointF(startPointF.x(), pointf.y())
        elif self._mousePos == 'TR':
            startPointF = QPointF(startPointF.x(), pointf.y())
            endPointF = QPointF(pointf.x(), endPointF.y())
        elif self._mousePos == 'L':
            startPointF = QPointF(pointf.x(), startPointF.y())
        elif self._mousePos == 'R':
            endPointF = QPointF(pointf.x(), endPointF.y())
        elif self._mousePos == 'BL':
            startPointF = QPointF(pointf.x(), startPointF.y())
            endPointF = QPointF(endPointF.x(), pointf.y())
        elif self._mousePos == 'B':
            endPointF = QPointF(endPointF.x(), pointf.y())
        elif self._mousePos == 'BR':
            endPointF = pointf
        else:  # 'ERROR'
            return
        newRectF = self.normalizeRectF(startPointF, endPointF)
        self.setCenterArea(newRectF.topLeft(), newRectF.bottomRight())

    def getMouseShapeBy(self, pointf):
        """根据鼠标位置返回对应的鼠标样式"""
        if self._rt_center.contains(pointf):
            if (self.screenshot_area.isDrawRectangle
                    or self.screenshot_area.isDrawEllipse
                    or self.screenshot_area.isDrawArrow
                    or self.screenshot_area.isDrawNumber):
                return Qt.CursorShape.ArrowCursor
            elif self.screenshot_area.isDrawGraffiti:
                return Qt.CursorShape.PointingHandCursor  # 超链接上的手势
            elif self.screenshot_area.isDrawText:
                return Qt.CursorShape.IBeamCursor  # 工字
            else:
                return Qt.CursorShape.SizeAllCursor  # 十字有箭头
                # return Qt.CursorShape.OpenHandCursor  # 打开的手，表示可拖拽
        elif self._square_topLeft.contains(pointf) or self._square_bottomRight.contains(pointf):
            return Qt.CursorShape.SizeFDiagCursor  # ↖↘
        elif self._square_topMid.contains(pointf) or self._square_bottomMid.contains(pointf):
            return Qt.CursorShape.SizeVerCursor  # ↑↓
        elif self._square_topRight.contains(pointf) or self._square_bottomLeft.contains(pointf):
            return Qt.CursorShape.SizeBDiagCursor  # ↙↗
        elif self._square_leftMid.contains(pointf) or self._square_rightMid.contains(pointf):
            return Qt.CursorShape.SizeHorCursor  # ←→
        else:
            return Qt.CursorShape.CrossCursor  # 十字无箭头

    def isMousePosInCenterRectF(self, pointf):
        return self._rt_center.contains(pointf)

    def paintMagnifyingGlassPixmap(self, pos, glassSize):
        """绘制放大镜内的图像(含纵横十字线)
        pos:鼠标光标位置
        glassSize:放大镜边框大小"""
        pixmapRect = QRect(0, 0, 20, 20)  # 以鼠标光标为中心的正方形区域，最好是偶数
        pixmapRect.moveCenter(pos)
        glassPixmap = self.physicalPixmap(pixmapRect)
        glassPixmap.setDevicePixelRatio(1.0)
        glassPixmap = glassPixmap.scaled(glassSize, glassSize, Qt.AspectRatioMode.KeepAspectRatio)
        # 在放大后的QPixmap上画纵横十字线
        self._painter.begin(glassPixmap)
        halfWidth = glassPixmap.width() / 2
        halfHeight = glassPixmap.height() / 2
        self._painter.setPen(self.screenshot_area.pen_center_line)
        self._painter.drawLine(QPointF(0, halfHeight), QPointF(glassPixmap.width(), halfHeight))
        self._painter.drawLine(QPointF(halfWidth, 0), QPointF(halfWidth, glassPixmap.height()))
        self._painter.end()
        return glassPixmap

    def paintEachEditAction(self, painter, textBorder=True):
        """绘制所有已保存的编辑行为。编辑行为超出截图区域也无所谓，保存图像时只截取截图区域内
        textBorder:是否绘制文本边框"""
        for action in self.getEditActions():
            if action[0] == 'rectangle':  # (type, color, lineWidth, startPoint, endPoint)
                self.paintRectangle(painter, action[1], action[2], action[3], action[4])
            elif action[0] == 'ellipse':  # (type, color, lineWidth, startPoint, endPoint)
                self.paintEllipse(painter, action[1], action[2], action[3], action[4])
            elif action[0] == 'arrow':  # (type, color, lineWidth, startPoint, endPoint)
                self.paintArrow(painter, action[1], action[2], action[3], action[4])
            elif action[0] == 'graffiti':  # (type, color, lineWidth, points)
                self.paintGraffiti(painter, action[1], action[2], action[3])
            elif action[0] == 'number':  # (type, color, lineWidth, points)
                self.paintNumber(painter, action[1])
            elif action[0] == 'text':  # (type, color, font, rectf, txt)
                self.paintTextInput(painter, action[1], action[2], action[3], action[4], textBorder=textBorder)

    def paintRectangle(self, painter, color, lineWidth, startPoint=None, endPoint=None):
        if not startPoint:
            startPoint = self._pt_startEdit
        if not endPoint:
            endPoint = self._pt_endEdit
        qrectf = self.normalizeRectF(startPoint, endPoint)
        if qrectf.isValid():
            pen = QPen(color)
            pen.setWidth(lineWidth)
            painter.setPen(pen)
            painter.setBrush(self.screenshot_area.color_transparent)
            painter.drawRect(qrectf)

    def paintArrow(self, painter, color, lineWidth, startPoint=None, endPoint=None):
        if not startPoint:
            startPoint = self._pt_startEdit
        if not endPoint:
            endPoint = self._pt_endEdit
        qrectf = self.normalizeRectF(startPoint, endPoint)
        if qrectf.isValid():
            pen = QPen(color)
            pen.setWidth(lineWidth)
            painter.setPen(pen)
            painter.setBrush(color)

            # 绘制直线
            painter.drawLine(startPoint, endPoint)

            # 计算箭头顶点的位置
            arrowSize = lineWidth * 4  # 箭头大小
            angle = math.atan2(endPoint.y() - startPoint.y(), endPoint.x() - startPoint.x())  # 直线的夹角
            arrowHead1 = QPointF(endPoint.x() - arrowSize * math.cos(angle) + arrowSize / 2 * math.sin(angle),
                                 endPoint.y() - arrowSize * math.sin(angle) - arrowSize / 2 * math.cos(angle))
            arrowHead2 = QPointF(endPoint.x() - arrowSize * math.cos(angle) - arrowSize / 2 * math.sin(angle),
                                 endPoint.y() - arrowSize * math.sin(angle) + arrowSize / 2 * math.cos(angle))

            # 绘制箭头
            arrowPath = QPainterPath()
            arrowPath.moveTo(arrowHead1)
            arrowPath.lineTo(endPoint)
            arrowPath.lineTo(arrowHead2)
            painter.drawPath(arrowPath)

    def paintEllipse(self, painter, color, lineWidth, startPoint=None, endPoint=None):
        if not startPoint:
            startPoint = self._pt_startEdit
        if not endPoint:
            endPoint = self._pt_endEdit
        qrectf = self.normalizeRectF(startPoint, endPoint)
        if qrectf.isValid():
            pen = QPen(color)
            pen.setWidth(lineWidth)
            painter.setPen(pen)
            painter.setBrush(self.screenshot_area.color_transparent)
            painter.drawEllipse(qrectf)

    def paintGraffiti(self, painter, color, lineWidth, pointfs=None):
        if not pointfs:
            pointfs = self.getGraffitiPointFs()
        pen = QPen(color)
        pen.setWidth(lineWidth)
        painter.setPen(pen)
        total = len(pointfs)
        if total == 0:
            return
        elif total == 1:
            painter.drawPoint(pointfs[0])
        else:
            previousPoint = pointfs[0]
            for i in range(1, total):
                nextPoint = pointfs[i]
                painter.drawLine(previousPoint, nextPoint)
                previousPoint = nextPoint

    def paintNumber(self, painter, number):
        number.paint(painter)

    def paintTextInput(self, painter, color, font, rectf, txt, textBorder=True):
        painter.setPen(color)
        painter.setFont(font)
        painter.drawText(rectf, txt, self._textOption)
        if textBorder:
            painter.setPen(Qt.PenStyle.DotLine)  # 点线
            painter.setBrush(self.screenshot_area.color_transparent)
            painter.drawRect(rectf)

    def getEditActions(self):
        return self._actions.copy()

    def takeTextInputActionAt(self, pointf):
        """根据鼠标位置查找已保存的文本输入结果，找到后取出"""
        for i in range(len(self._actions)):
            action = self._actions[i]
            if action[0] == 'text' and action[3].contains(pointf):
                return self._actions.pop(i)
        return None

    def undoEditAction(self):
        reply = False

        if self._actions:
            reply = self._actions.pop()
            if not self._actions:  # 所有编辑行为都被撤销后退出编辑模式
                self.screenshot_area.exitEditMode()
        else:
            self.screenshot_area.exitEditMode()
        return reply

    def clearEditActions(self):
        self._actions.clear()

    def setBeginEditPoint(self, pointf):
        """在截图区域上绘制矩形、椭圆时鼠标左键按下的位置（topLeft）"""
        self._pt_startEdit = pointf
        self.screenshot_area.isDrawing = True

    def setEndEditPoint(self, pointf):
        """在截图区域上绘制矩形、椭圆时鼠标左键松开的位置（bottomRight）"""
        self._pt_endEdit = pointf

    def saveRectangleAction(self):
        self._actions.append(('rectangle', self.screenshot_area.toolbar.current_color(),
                              self.screenshot_area.toolbar.current_line_width(),
                              self._pt_startEdit, self._pt_endEdit))
        self._pt_startEdit = QPointF()
        self._pt_endEdit = QPointF()
        self.screenshot_area.isDrawing = False

    def saveArrowAction(self):
        self._actions.append(('arrow', self.screenshot_area.toolbar.current_color(),
                              self.screenshot_area.toolbar.current_line_width(),
                              self._pt_startEdit, self._pt_endEdit))
        self._pt_startEdit = QPointF()
        self._pt_endEdit = QPointF()
        self.screenshot_area.isDrawing = False

    def saveEllipseAction(self):
        self._actions.append(('ellipse',
                              self.screenshot_area.toolbar.current_color(),
                              self.screenshot_area.toolbar.current_line_width(),
                              self._pt_startEdit, self._pt_endEdit))
        self._pt_startEdit = QPointF()
        self._pt_endEdit = QPointF()
        self.screenshot_area.isDrawing = False

    def saveGraffitiPointF(self, pointf, first=False):
        self._pointfs.append(pointf)
        if first:
            self.screenshot_area.isDrawing = True

    def getGraffitiPointFs(self):
        return self._pointfs.copy()

    def saveGraffitiAction(self):
        if self._pointfs:
            self._actions.append(('graffiti',
                                  self.screenshot_area.toolbar.current_color(),
                                  self.screenshot_area.toolbar.current_line_width(),
                                  self._pointfs.copy()))
            self._pointfs.clear()
            self.screenshot_area.isDrawing = False

    def setBeginInputTextPoint(self, pointf):
        """在截图区域上输入文字时鼠标左键按下的位置（topLeft）"""
        self.screenshot_area.isDrawing = True
        self.screenshot_area.textInputWg.beginNewInput(pointf, self._pt_end)

    def saveNumberAction(self, number):
        self._actions.append(('number', number))
        self.screenshot_area.isDrawing = False

    def saveTextInputAction(self):
        txt = self.screenshot_area.textInputWg.toPlainText()
        if txt:
            rectf = self.screenshot_area.textInputWg.max_rect  # 取最大矩形的topLeft
            rectf.setSize(QRectF(self.screenshot_area.textInputWg.rect()).size())  # 取实际矩形的宽高
            self._actions.append(('text', self.screenshot_area.toolbar.current_color(),
                                  self.screenshot_area.toolbar.current_font(), rectf, txt))
            self.screenshot_area.textInputWg.clear()
        self.screenshot_area.textInputWg.hide()  # 不管保存成功与否都取消编辑
        self.screenshot_area.isDrawing = False


class ScreenShotWidget(QWidget):
    send_pixmap_signal = pyqtSignal(QPixmap, QPoint)
    fileType_all = '所有文件 (*);;Excel文件 (*.xls *.xlsx);;图片文件 (*.jpg *.jpeg *.gif *.png *.bmp)'
    fileType_img = '图片文件 (*.jpg *.jpeg *.gif *.png *.bmp)'
    dir_lastAccess = os.getcwd()  # 最后访问目录

    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.setWindowIcon(QIcon(self.settings.get('SoftwareConfig', 'exe_icon')))
        self.setMouseTracking(True)
        self.setWindowFlags(Qt.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.initPainterTool()
        self.initFunctionalFlag()
        self.initShortKeys()
        self.screenArea = ScreenArea(self)
        self.toolbar = ScreenShotToolBar(self)
        self.textInputWg = TextInputWidget(self)
        self.circles = []
        self.currentCircle = None

    def start(self):
        self.screenArea.captureScreen()
        self.setGeometry(self.screenArea.screenPhysicalRectF().toRect())
        self.clearScreenShotArea()
        self.showFullScreen()

    def initPainterTool(self):
        self.painter = QPainter()
        self.color_transparent = Qt.GlobalColor.transparent
        self.color_black = QColor(0, 0, 0, 128)  # 黑色背景
        self.color_lightBlue = QColor(0, 116, 217)  # 蓝色
        # 创建调色板对象并设置字体颜色
        self.font_normal = QFont('Times New Roman', 11, QFont.Weight.Normal)
        self.font_textInput = QFont('微软雅黑', 16, QFont.Weight.Normal)  # 工具条文字工具默认字体
        self.pen_transparent = QPen(Qt.PenStyle.NoPen)  # 没有笔迹，画不出线条
        self.pen_white = QPen(Qt.GlobalColor.white)
        self.pen_center_line = QPen(self.color_lightBlue)  # 实线，浅蓝色
        self.pen_center_line.setStyle(Qt.PenStyle.SolidLine)
        self.pen_center_line.setWidthF(1)
        self.pen_border_line = QPen(self.color_lightBlue)  # 浅蓝色
        self.pen_border_line.setStyle(Qt.PenStyle.SolidLine)
        self.pen_border_line.setWidthF(3)

    def initFunctionalFlag(self):
        self.hasScreenShot = False  # 是否已通过拖动鼠标左键划定截图区域
        self.isCapturing = False  # 正在拖动鼠标左键选定截图区域时
        self.isMoving = False  # 在截图区域内拖动时
        self.isAdjusting = False  # 在截图区域的边框按住鼠标左键调整大小时
        self.isDrawing = False  # 是否已在截图区域内开始绘制
        self.isDrawRectangle = False  # 正在截图区域内画矩形
        self.isDrawEllipse = False  # 正在截图区域内画椭圆
        self.isDrawArrow = False  # 正在截图区域内画箭头
        self.isDrawGraffiti = False  # 正在截图区域内进行涂鸦
        self.isDrawNumber = False  # 正在截图区域内绘制序号
        self.isDrawText = False  # 正在截图区域内画文字
        self.setCursor(Qt.CursorShape.CrossCursor)  # 设置鼠标样式 十字

    def initShortKeys(self):
        self.cancel_key = QKeySequence(self.settings.get('ShortKeySettings', 'cancel'))
        self.copy_key = QKeySequence(self.settings.get('ShortKeySettings', 'copy'))
        self.save_key = QKeySequence(self.settings.get('ShortKeySettings', 'save'))
        self.undo_key = QKeySequence(self.settings.get('ShortKeySettings', 'undo'))

    def paintEvent(self, event):
        centerRectF = self.screenArea.centerLogicalRectF()
        screenSizeF = self.screenArea.screenLogicalSizeF()
        canvasPixmap = self.screenArea.screenPhysicalPixmapCopy()
        # 在屏幕截图的副本上绘制已选定的截图区域
        self.painter.begin(canvasPixmap)
        if self.hasScreenShot:
            self.paintCenterArea(centerRectF)  # 绘制中央截图区域
            self.paintMaskLayer(screenSizeF, fullScreen=False)  # 绘制截图区域的周边区域遮罩层
        else:
            self.paintMaskLayer(screenSizeF)
        self.paintMagnifyingGlass(screenSizeF)  # 在鼠标光标右下角显示放大镜
        self.paintToolbar(centerRectF, screenSizeF)  # 在截图区域右下角显示工具条
        self.paintEditActions()  # 在截图区域绘制编辑行为结果
        self.painter.end()
        # 把画好的绘制结果显示到窗口上
        self.painter.begin(self)
        self.painter.drawPixmap(0, 0, canvasPixmap)  # 从坐标(0, 0)开始绘制
        self.painter.end()

    def paintCenterArea(self, centerRectF):
        """绘制已选定的截图区域"""
        self.painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # 反走样
        # 1.绘制矩形线框
        self.painter.setPen(self.pen_border_line)
        self.painter.drawRect(centerRectF)
        # 2.绘制矩形线框4个端点和4条边框的中间点
        if centerRectF.width() >= 100 and centerRectF.height() >= 100:
            points = [  # 点坐标
                centerRectF.topLeft(), centerRectF.topRight(), centerRectF.bottomLeft(), centerRectF.bottomRight(),
                self.screenArea.centerLeftMid(), self.screenArea.centerRightMid(),
                self.screenArea.centerTopMid(), self.screenArea.centerBottomMid()
            ]
            blueDotRadius = QPointF(3, 3)  # 椭圆蓝点
            self.painter.setBrush(self.color_lightBlue)
            for point in points:
                self.painter.drawEllipse(QRectF(point - blueDotRadius, point + blueDotRadius))
        # 3.在截图区域左上角显示截图区域宽高
        if centerRectF.topLeft().y() > 20:
            labelPos = centerRectF.topLeft() + QPointF(5, -5)
        else:  # 拖拽截图区域到贴近屏幕上边缘时“宽x高”移动到截图区域左上角的下侧
            labelPos = centerRectF.topLeft() + QPointF(5, 15)
        centerPhysicalRect = self.screenArea.centerPhysicalRectF().toRect()
        self.painter.setPen(self.pen_white)
        self.painter.setFont(self.font_normal)
        self.painter.drawText(labelPos, '宽高：%s × %s' % (centerPhysicalRect.width(), centerPhysicalRect.height()))
        # 4.在屏幕左上角预览截图结果
        # self.painter.drawPixmap(0, 0, self.screenArea.centerPhysicalPixmap())  # 从坐标(0, 0)开始绘制

    def paintMaskLayer(self, screenSizeF, fullScreen=True):
        if fullScreen:  # 全屏遮罩层
            maskPixmap = QPixmap(screenSizeF.toSize())
            maskPixmap.fill(self.color_black)
            self.painter.drawPixmap(0, 0, maskPixmap)
        else:  # 绘制截图区域的周边区域遮罩层，以凸显截图区域
            for area in self.screenArea.aroundAreaWithoutIntersection():
                maskPixmap = QPixmap(area.size().toSize())
                maskPixmap.fill(self.color_black)
                self.painter.drawPixmap(area.topLeft(), maskPixmap)

    def paintMagnifyingGlass(self, screenSizeF, glassSize=230, offset=30, labelHeight=100):
        """
        在没有截图区域模式、正在截取区域或调整截取区域大小时，在鼠标光标右下角显示放大镜
        glassSize: 放大镜正方形边长
        offset: 放大镜端点距离鼠标光标位置的最近距离
        labelHeight: pos 和 rgb 两行文字的高度
        """
        if self.hasScreenShot and (not self.isCapturing) and (not self.isAdjusting):
            return
        # 获取光标位置
        pos = QCursor.pos()
        # 绘制放大镜内部的 QPixmap，包含纵横十字线
        glassPixmap = self.screenArea.paintMagnifyingGlassPixmap(pos, glassSize)
        # 限制放大镜显示在屏幕范围内
        glassRect = glassPixmap.rect()
        if (pos.x() + glassSize + offset) < screenSizeF.width():
            if (pos.y() + offset + glassSize + labelHeight) < screenSizeF.height():
                glassRect.moveTo(pos + QPoint(offset, offset))
            else:
                glassRect.moveBottomLeft(pos + QPoint(offset, -offset))
        else:
            if (pos.y() + offset + glassSize + labelHeight) < screenSizeF.height():
                glassRect.moveTopRight(pos + QPoint(-offset, offset))
            else:
                glassRect.moveBottomRight(pos + QPoint(-offset, -offset))
        # 绘制放大镜
        self.painter.drawPixmap(glassRect.topLeft(), glassPixmap)

        # 获取放大镜内中心像素的 RGB 值
        rgb_obj = QRgba64.fromArgb32(glassPixmap.toImage().pixel(glassPixmap.rect().center()))
        self.color_rgb8 = (rgb_obj.red8(), rgb_obj.green8(), rgb_obj.blue8())
        self.color_hex = "#{:02X}{:02X}{:02X}".format(*self.color_rgb8)
        self.cur_pos = (pos.x(), pos.y())
        # 绘制放大镜底部标签
        labelRectF = QRectF(glassRect.bottomLeft().x(), glassRect.bottomLeft().y() - 10, glassSize, labelHeight)
        self.painter.setPen(QPen(Qt.NoPen))
        self.painter.setBrush(QColor(0, 0, 0, 150))  # 半透明黑底
        self.painter.drawRoundedRect(labelRectF, 12, 12)  # 使用圆角矩形
        self.painter.setPen(QColor(255, 255, 255))
        self.painter.setFont(self.font_normal)
        self.painter.drawText(
            labelRectF.adjusted(12, 6, -5, -5),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            f'坐标：({", ".join(str(i) for i in self.cur_pos)})\n'
            f'RGB：{", ".join(str(i) for i in self.color_rgb8)}\n'
            f'HEX：{self.color_hex}'
        )

    def paintToolbar(self, centerRectF, screenSizeF):
        """在截图区域右下角显示工具条"""
        if self.hasScreenShot:
            if self.isCapturing or self.isAdjusting:
                self.toolbar.hide()  # 正在划定截取区域时、调整截图区域大小时不显示工具条
            else:
                self.toolbar.adjustSize()
                toolbarRectF = QRectF(self.toolbar.rect())
                # 工具条位置优先顺序：右下角下侧，右上角上侧，右下角上侧
                if (screenSizeF.height() - centerRectF.bottomRight().y()) > toolbarRectF.height():
                    toolbarRectF.moveTopRight(centerRectF.bottomRight() + QPointF(-5, 5))
                elif centerRectF.topRight().y() > toolbarRectF.height():
                    toolbarRectF.moveBottomRight(centerRectF.topRight() + QPointF(-5, -5))
                else:
                    toolbarRectF.moveBottomRight(centerRectF.bottomRight() + QPointF(-5, -5))
                # 限制工具条的x坐标不为负数，不能移出屏幕外
                if toolbarRectF.x() < 0:
                    pos = toolbarRectF.topLeft()
                    pos.setX(centerRectF.x() + 5)
                    toolbarRectF.moveTo(pos)
                self.toolbar.move(toolbarRectF.topLeft().toPoint())
                self.toolbar.show()
        else:
            self.toolbar.hide()

    def paintEditActions(self):
        """在截图区域绘制编辑行为结果。编辑行为超出截图区域也无所谓，保存图像时只截取截图区域内"""
        # 1.绘制正在拖拽编辑中的矩形、椭圆、涂鸦
        if self.isDrawRectangle:
            self.screenArea.paintRectangle(self.painter, self.toolbar.current_color(),
                                           self.toolbar.current_line_width())
        elif self.isDrawArrow:
            self.screenArea.paintArrow(self.painter, self.toolbar.current_color(), self.toolbar.current_line_width())
        elif self.isDrawEllipse:
            self.screenArea.paintEllipse(self.painter, self.toolbar.current_color(), self.toolbar.current_line_width())
        elif self.isDrawGraffiti:
            self.screenArea.paintGraffiti(self.painter, self.toolbar.current_color(), self.toolbar.current_line_width())
        # 2.绘制所有已保存的编辑行为
        self.screenArea.paintEachEditAction(self.painter)

    def clearEditFlags(self):
        self.isDrawing = False
        self.isDrawRectangle = False
        self.isDrawEllipse = False
        self.isDrawArrow = False
        self.isDrawGraffiti = False
        self.isDrawNumber = False
        self.isDrawText = False
        Circle.destroyAll()

    def exitEditMode(self):
        """退出编辑模式"""
        self.clearEditFlags()
        self.toolbar.on_action_triggered()  # 清空工具条工具按钮选中状态
        self.textInputWg.hide()

    def clearScreenShotArea(self):
        """清空已划定的截取区域"""
        self.screenArea.clearEditActions()  # 清除已保存的编辑行为
        self.exitEditMode()
        self.hasScreenShot = False
        self.isCapturing = False
        pos = QPointF()
        self.screenArea.setCenterArea(pos, pos)
        self.update()
        self.setCursor(Qt.CursorShape.CrossCursor)  # 设置鼠标样式 十字

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:  # 左键触发
            pos = event.pos()
            if self.hasScreenShot:
                if self.isDrawRectangle or self.isDrawEllipse or self.isDrawArrow:
                    self.screenArea.setBeginEditPoint(pos)
                elif self.isDrawGraffiti:  # 保存涂鸦经过的每一个点
                    self.screenArea.saveGraffitiPointF(pos, first=True)
                elif self.isDrawNumber:
                    self.currentCircle = Circle(event.pos(),
                                                self.toolbar.current_color(),
                                                self.toolbar.current_line_width(),
                                                self.toolbar.current_line_width() * 5)
                elif self.isDrawText:
                    if self.isDrawing:
                        if QRectF(self.textInputWg.rect()).contains(pos):
                            pass  # 在输入框内调整光标位置，忽略
                        else:  # 鼠标点到输入框之外，完成编辑
                            self.screenArea.saveTextInputAction()
                    else:  # 未开始编辑时（暂不支持文本拖拽）
                        action = self.screenArea.takeTextInputActionAt(pos)
                        if action:  # 鼠标点到输入框之内，修改旧的文本输入
                            self.textInputWg.loadTextInputBy(action)
                        else:  # 鼠标点到输入框之外，开始新的文本输入
                            self.screenArea.setBeginInputTextPoint(pos)
                elif self.screenArea.isMousePosInCenterRectF(pos):
                    self.isMoving = True  # 进入拖拽移动模式
                    self.screenArea.setBeginDragPoint(pos)
                else:
                    self.isAdjusting = True  # 进入调整大小模式
                    self.screenArea.setBeginAdjustPoint(pos)
            else:
                self.screenArea.setCenterArea(pos, pos)
                self.isCapturing = True  # 进入划定截图区域模式
        if event.button() == Qt.MouseButton.RightButton:  # 右键触发
            if self.hasScreenShot or self.isCapturing:  # 清空已划定的的截图区域
                self.clearScreenShotArea()
            else:
                self.hide()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.isDrawRectangle:
                self.screenArea.saveRectangleAction()
            elif self.isDrawArrow:
                self.screenArea.saveArrowAction()
            elif self.isDrawEllipse:
                self.screenArea.saveEllipseAction()
            elif self.isDrawGraffiti:
                self.screenArea.saveGraffitiAction()
            elif self.isDrawNumber:
                self.screenArea.saveNumberAction(self.currentCircle)

            self.isCapturing = False
            self.isMoving = False
            self.isAdjusting = False
            self.toolbar.show()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if self.isDrawing:
            if self.isDrawRectangle or self.isDrawEllipse or self.isDrawArrow:
                self.screenArea.setEndEditPoint(pos)
            elif self.isDrawGraffiti:
                self.screenArea.saveGraffitiPointF(pos)
        elif self.isCapturing:
            self.hasScreenShot = True
            self.screenArea.setEndPoint(pos, remake=True)
        elif self.isMoving:
            self.screenArea.moveCenterAreaTo(pos)
        elif self.isAdjusting:
            self.screenArea.adjustCenterAreaBy(pos)
        self.update()
        if self.hasScreenShot:
            self.setCursor(self.screenArea.getMouseShapeBy(pos))
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)  # 设置鼠标样式 十字

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.screenArea.isMousePosInCenterRectF(event.pos()):
                self.save2Clipboard()
                self.hide()

    def keyPressEvent(self, event):
        if QKeySequence.matches(self.cancel_key, event.modifiers() | event.key()):
            self.hide()
        if QKeySequence.matches(self.copy_key, event.modifiers() | event.key()) or event.key() in (
                Qt.Key.Key_Return, Qt.Key.Key_Enter):  # 大键盘、小键盘回车
            self.save2Clipboard()
        if QKeySequence.matches(self.save_key, event.modifiers() | event.key()):
            self.save2Local()
        if QKeySequence.matches(self.undo_key, event.modifiers() | event.key()):
            self.toolbar.undo()

    def save2Clipboard(self):
        """将截图区域复制到剪贴板"""
        mimData = QMimeData()
        if self.hasScreenShot:
            mimData.setImageData(self.screenArea.centerPhysicalPixmap().toImage())
            QApplication.clipboard().setMimeData(mimData)
        else:
            mimData.setText(f'坐标：({", ".join(str(i) for i in self.cur_pos)})\n'
                            f'RGB：{", ".join(str(i) for i in self.color_rgb8)}\n'
                            f'HEX：{self.color_hex}')
            QApplication.clipboard().setMimeData(mimData)
        self.hide()

    def save2Local(self):
        self.settings = Settings()
        fileType = self.fileType_img
        if self.settings.get('SaveSettings', 'is_silent_save') == 'True':
            fileFolder = Path(self.settings.get('SaveSettings', 'default_path_edit'))
            module = self.settings.get('SaveSettings', 'save_name_edit')
            fileName = self.sys_getCurTime(self.settings.module_parser(module))
            filePath = str(fileFolder / fileName)
        else:
            filePath, fileFormat = self.sys_selectSaveFilePath(self, fileType=fileType)
        if filePath:
            quality = int(self.settings.get('GeneralSettings', 'picture_quality'))
            self.screenArea.centerPhysicalPixmap().save(filePath, quality=quality)
            self.hide()

    def pinned_to_top(self):
        self.send_pixmap_signal.emit(self.screenArea.centerPhysicalPixmap(), self.screenArea._pt_start)
        self.hide()

    def sys_getCurTime(self, fmt='%Y-%m-%d %H:%M:%S'):
        """获取字符串格式的当前时间"""
        return datetime.now().strftime(fmt)

    def sys_selectSaveFilePath(self, widget, title='选择文件保存路径', saveFileDir=None,
                               saveFileName='', fileType=None):
        """选择文件保存路径"""
        options = QFileDialog.Option.ReadOnly
        if saveFileName == '':
            module = self.settings.get('SaveSettings', 'save_name_edit')
            saveFileName = self.sys_getCurTime(self.settings.module_parser(module))
        if not saveFileDir:
            saveFileDir = self.dir_lastAccess
        saveFilePath = os.path.join(saveFileDir, saveFileName)
        if not fileType:
            fileType = self.fileType_all
        filePath, fileFormat = QFileDialog.getSaveFileName(widget, title, saveFilePath, fileType, options=options)
        if filePath:
            self.dir_lastAccess = os.path.dirname(filePath)
        return filePath, fileFormat
