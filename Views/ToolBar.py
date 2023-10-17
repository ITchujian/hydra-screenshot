from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtWidgets import QToolBar, QAction

from Functions import LineWidthAction, FontAction, ColorAction
from Settings import Settings
from .LongScreenshot import LongScreenshot


class ScreenShotToolBar(QToolBar):
    """截图区域工具条"""

    def __init__(self, screenshot_area):
        super().__init__(screenshot_area)
        self.settings = Settings()
        self.screenshot_area = screenshot_area
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setStyleSheet("QToolBar {border-radius: 6px;padding: 3px;background-color: #ffffff;}"
                           "QToolBar QToolButton {min-width: 42px;min-height: 42px;}")

        self.normal_style = "QToolBar QToolButton{color: black;}"
        self.selected_style = "QToolBar QToolButton{color: #b35f27;border-radius: 4px;background-color: #f0f0f0}"

        self.number = 1

        self.icon_pixmap = QPixmap(32, 32)
        self.icon_pixmap.fill(self.screenshot_area.color_transparent)
        self.__icon_pixmap_center = QPointF(self.icon_pixmap.rect().center())

        self.small_line_width = int(self.settings.get('AnnotationSettings', 'thin_width'))
        self.normal_line_width = int(self.settings.get('AnnotationSettings', 'medium_width'))
        self.big_line_width = int(self.settings.get('AnnotationSettings', 'thick_width'))
        self.__current_line_width = self.normal_line_width

        self.thin_line = LineWidthAction('细', self, self.small_line_width)
        self.medium_line = LineWidthAction('中', self, self.normal_line_width)
        self.thick_line = LineWidthAction('粗', self, self.big_line_width)

        self.font_action = FontAction(QIcon(self.settings.get('IconPaths', 'font_setting_icon')), '字体', self)
        self.default_color = QColor()
        self.default_color.setNamedColor(self.settings.get('AnnotationSettings', 'default_color'))
        self.color_action = ColorAction('颜色', self.default_color, parent=self)

        self.rectangle_action = QAction(QIcon(self.settings.get('IconPaths', 'rectangle_icon')), '矩形', self)
        self.ellipse_action = QAction(QIcon(self.settings.get('IconPaths', 'ellipse_icon')), '圆形', self)
        self.arrow_action = QAction(QIcon(self.settings.get('IconPaths', 'arrow_icon')), '箭头', self)
        self.graffiti_action = QAction(QIcon(self.settings.get('IconPaths', 'graffiti_icon')), '绘制', self)
        self.number_action = QAction(QIcon(self.settings.get('IconPaths', 'number_icon')), '序号', self)
        self.text_input_action = QAction(QIcon(self.settings.get('IconPaths', 'text_icon')), '文本', self)
        self.undo_action = QAction(QIcon(self.settings.get('IconPaths', 'undo_icon')), '撤销', self)
        self.tongs_action = QAction(QIcon(self.settings.get('IconPaths', 'tongs_icon')), '取消编辑', self)
        self.long_action = QAction(QIcon(self.settings.get('IconPaths', 'long_icon')), '长截图', self)
        self.save_action = QAction(QIcon(self.settings.get('IconPaths', 'save_icon')), '保存', self)
        self.to_top_action = QAction(QIcon(self.settings.get('IconPaths', 'to_top_icon')), '贴图置顶', self)
        self.close_action = QAction(QIcon(self.settings.get('IconPaths', 'cancel_icon')), '关闭', self)
        self.copy_action = QAction(QIcon(self.settings.get('IconPaths', 'ok_icon')), '复制', self)

        self.rectangle_action.triggered.connect(self.before_draw_rectangle)
        self.ellipse_action.triggered.connect(self.before_draw_ellipse)
        self.arrow_action.triggered.connect(self.before_draw_arrow)
        self.graffiti_action.triggered.connect(self.before_draw_graffiti)
        self.number_action.triggered.connect(self.before_draw_number)
        self.text_input_action.triggered.connect(self.before_draw_text)
        self.undo_action.triggered.connect(self.undo)
        self.tongs_action.triggered.connect(self.cancel_edit)
        self.long_action.triggered.connect(self.long_screenshot)
        self.save_action.triggered.connect(lambda: self.before_save('local'))
        self.to_top_action.triggered.connect(self.to_top)
        self.close_action.triggered.connect(self.exit)
        self.copy_action.triggered.connect(lambda: self.before_save('clipboard'))

        self.addAction(self.thin_line)
        self.addAction(self.medium_line)
        self.addAction(self.thick_line)
        self.addAction(self.font_action)
        self.addAction(self.color_action)
        self.separator1 = self.addSeparator()
        self.addAction(self.rectangle_action)
        self.addAction(self.ellipse_action)
        self.addAction(self.arrow_action)
        self.addAction(self.graffiti_action)
        self.addAction(self.number_action)
        self.addAction(self.text_input_action)
        self.separator2 = self.addSeparator()
        self.addAction(self.undo_action)
        self.addAction(self.tongs_action)
        self.separator3 = self.addSeparator()
        self.addAction(self.long_action)
        self.addAction(self.save_action)
        self.addAction(self.to_top_action)
        self.addAction(self.close_action)
        self.addAction(self.copy_action)
        self.actionTriggered.connect(self.on_action_triggered)
        self.long_screenshot = None
        self.color_action.setVisible(False)
        self.separator1.setVisible(False)


    def exit(self):
        self.screenshot_area.hide()

    def current_line_width(self):
        return self.__current_line_width

    def set_current_line_width(self, line_width):
        self.__current_line_width = line_width

    def current_font(self):
        return self.font_action.curFont

    def current_color(self):
        return self.color_action.curColor

    def icon_pixmap_copy(self):
        return self.icon_pixmap.copy()

    def icon_pixmap_center(self):
        return self.__icon_pixmap_center

    def on_action_triggered(self):
        """突出显示已选中的画笔粗细、编辑模式"""
        for line_action in [self.thin_line, self.medium_line, self.thick_line]:
            if line_action.lineWidth == self.current_line_width:
                self.widgetForAction(line_action).setStyleSheet(self.selected_style)
            else:
                self.widgetForAction(line_action).setStyleSheet(self.normal_style)

        if self.screenshot_area.isDrawRectangle:
            self.widgetForAction(self.rectangle_action).setStyleSheet(self.selected_style)
        else:
            self.widgetForAction(self.rectangle_action).setStyleSheet(self.normal_style)

        if self.screenshot_area.isDrawArrow:
            self.widgetForAction(self.arrow_action).setStyleSheet(self.selected_style)
        else:
            self.widgetForAction(self.arrow_action).setStyleSheet(self.normal_style)

        if self.screenshot_area.isDrawEllipse:
            self.widgetForAction(self.ellipse_action).setStyleSheet(self.selected_style)
        else:
            self.widgetForAction(self.ellipse_action).setStyleSheet(self.normal_style)

        if self.screenshot_area.isDrawGraffiti:
            self.widgetForAction(self.graffiti_action).setStyleSheet(self.selected_style)
        else:
            self.widgetForAction(self.graffiti_action).setStyleSheet(self.normal_style)

        if self.screenshot_area.isDrawNumber:
            self.widgetForAction(self.number_action).setStyleSheet(self.selected_style)
        else:
            self.widgetForAction(self.number_action).setStyleSheet(self.normal_style)

        if self.screenshot_area.isDrawText:
            self.widgetForAction(self.text_input_action).setStyleSheet(self.selected_style)
        else:
            self.widgetForAction(self.text_input_action).setStyleSheet(self.normal_style)

    def set_line_width_action_visible(self, flag):
        self.thin_line.setVisible(flag)
        self.medium_line.setVisible(flag)
        self.thick_line.setVisible(flag)

    def before_draw_rectangle(self):
        self.screenshot_area.clearEditFlags()
        self.screenshot_area.isDrawRectangle = True
        self.set_line_width_action_visible(True)
        self.color_action.setVisible(True)
        self.font_action.setVisible(False)
        self.separator1.setVisible(True)

    def before_draw_ellipse(self):
        self.screenshot_area.clearEditFlags()
        self.screenshot_area.isDrawEllipse = True
        self.set_line_width_action_visible(True)
        self.color_action.setVisible(True)
        self.font_action.setVisible(False)
        self.separator1.setVisible(True)

    def before_draw_arrow(self):
        self.screenshot_area.clearEditFlags()
        self.screenshot_area.isDrawArrow = True
        self.set_line_width_action_visible(True)
        self.color_action.setVisible(True)
        self.font_action.setVisible(False)
        self.separator1.setVisible(True)

    def before_draw_graffiti(self):
        self.screenshot_area.clearEditFlags()
        self.screenshot_area.isDrawGraffiti = True
        self.set_line_width_action_visible(True)
        self.color_action.setVisible(True)
        self.font_action.setVisible(False)
        self.separator1.setVisible(True)

    def before_draw_number(self):
        self.screenshot_area.clearEditFlags()
        self.screenshot_area.isDrawNumber = True
        self.set_line_width_action_visible(True)
        self.color_action.setVisible(True)
        self.font_action.setVisible(False)
        self.separator1.setVisible(True)

    def before_draw_text(self):
        self.screenshot_area.clearEditFlags()
        self.screenshot_area.isDrawText = True
        self.set_line_width_action_visible(False)
        self.color_action.setVisible(True)
        self.font_action.setVisible(True)
        self.separator1.setVisible(True)

    def undo(self):
        """撤销上次编辑行为"""
        if self.screenshot_area.screenArea.undoEditAction():
            self.screenshot_area.update()

    def cancel_edit(self):
        self.screenshot_area.clearEditFlags()
        self.set_line_width_action_visible(False)
        self.font_action.setVisible(False)
        self.color_action.setVisible(False)
        self.separator1.setVisible(False)

    def long_screenshot(self):
        self.screenshot_area.clearEditFlags()
        center_rectf = self.screenshot_area.screenArea.centerLogicalRectF()
        self.exit()
        self.long_screenshot = LongScreenshot(center_rectf)
        self.long_screenshot.show()

    def before_save(self, target):
        # 若正在编辑文本未保存，先完成编辑
        if self.screenshot_area.isDrawing and self.screenshot_area.isDrawText:
            self.screenshot_area.saveTextInputAction()

        if target == 'local':
            self.screenshot_area.save2Local()
        elif target == 'clipboard':
            self.screenshot_area.save2Clipboard()

    def to_top(self):
        self.screenshot_area.pinned_to_top()

    def enterEvent(self, event):
        self.screenshot_area.setCursor(Qt.CursorShape.ArrowCursor)  # 工具条上显示标准箭头cursor

    def leaveEvent(self, event):
        self.screenshot_area.setCursor(Qt.CursorShape.CrossCursor)  # 十字无箭头
