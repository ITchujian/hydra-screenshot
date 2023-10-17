import math

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainterPath, QPainter, QColor, QIntValidator, QPen, QKeySequence, QKeyEvent
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QLabel, QCheckBox, QLineEdit, \
    QSpinBox, QPushButton, QSizePolicy, QFileDialog, QColorDialog
from .BaseWindow import BaseWidget


class ShortcutWidget(QWidget):
    non_standard = (
        'Backspace', 'Tab', 'Enter', 'Space', 'CapsLock', 'Shift', 'Ctrl', 'Alt', 'ContextMenu',
        'Pause',
        'Insert', 'Home', 'PageUp', 'Delete', 'End', 'PageDown', 'PrintScreen', 'ScrollLock', 'NumLock',
        'F1', 'F2',
        'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'Super', 'Apps', 'Sleep')

    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建 QLabel 用于显示快捷键组合
        self.shortcut_label = QLabel("")
        self.shortcut_label.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        shortcut_layout = QVBoxLayout(self)
        shortcut_layout.addWidget(self.shortcut_label)
        self.setLayout(shortcut_layout)
        # 标记是否选中控件
        self.selected = False
        # 允许控件以鼠标单击获得焦点
        self.setFocusPolicy(Qt.ClickFocus)
        self.setStyleSheet(
            "border-radius: 5px;background-color: #ffffff;border: 2px solid #007aff;color: #007aff;")

    def keyPressEvent(self, event: QKeyEvent):
        if self.selected:
            modifiers = event.modifiers()
            key = event.key()
            shortcut_sequence = QKeySequence(Qt.KeyboardModifier(modifiers) | Qt.Key(key))
            shortcut_text = shortcut_sequence.toString(QKeySequence.PortableText)
            if shortcut_text not in self.non_standard:
                self.shortcut_label.setText(shortcut_text)

    def mousePressEvent(self, event):
        # 切换选中状态
        if not self.selected:
            # 取消其他已选中的 ShortcutWidget
            parent = self.parentWidget()
            for child in parent.children():
                if isinstance(child, ShortcutWidget) and child.selected:
                    child.selected = False
                    child.updateStyle()
            # 选中当前的 ShortcutWidget
            self.selected = True
            self.updateStyle()
        event.accept()

    def updateStyle(self):
        if self.selected:
            self.shortcut_label.setText("请按下快捷键")
            self.setStyleSheet(
                "border-radius: 5px;background-color: #007aff;border: 2px solid #007aff;color: #ffffff;")  # 恢复默认样式
        else:
            self.shortcut_label.setText(self.before_text)
            self.setStyleSheet(
                "border-radius: 5px;background-color: #ffffff;border: 2px solid #007aff;color: #007aff;")

    def text(self):
        text = self.shortcut_label.text()
        if text == "请按下快捷键":
            return self.before_text
        return text

    def setText(self, text: str):
        self.shortcut_label.setText(text)
        self.before_text = text  # 记录更改前的


class LinePreview(QWidget):
    def __init__(self):
        super().__init__()
        self.lineWidth = 1
        self.lineColor = Qt.GlobalColor.red
        self.setMaximumHeight(30)
        self.setFixedWidth(120)

    def refresh(self, lineWidth, lineColor):
        self.lineWidth = lineWidth
        self.lineColor = lineColor
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿
        # 绘制轮廓
        pen = QPen()
        pen.setColor(QColor(0, 123, 255))  # 设置轮廓颜色为蓝色
        painter.setPen(pen)
        painter.drawRect(self.rect())  # 绘制边缘轮廓
        # 绘制波浪线
        pen.setColor(self.lineColor)  # 设置线条颜色为红色
        pen.setWidth(self.lineWidth)
        painter.setPen(pen)
        wave_amplitude = 3  # 波浪线的幅度
        wave_period = 9  # 波浪线的周期
        wave_height = self.height() / 2  # 波浪线的高度（垂直位置）
        path = QPainterPath()
        y = wave_amplitude + wave_height
        path.moveTo(0, y)  # 添加起始点
        for x in range(1, self.width(), 1):
            y = wave_amplitude * (1 + math.sin(x / wave_period)) + wave_height
            path.lineTo(x, y)  # 连接波浪线上的点
        painter.drawPath(path)


class SettingWindow(BaseWidget):
    def __init__(self, settings=None):
        super().__init__(title="软件设置")
        self.settings = settings
        self.tab_widget = QTabWidget(self)
        self.apply_button = QPushButton("应用", self)
        self.apply_button.setObjectName('apply')
        self.cancel_button = QPushButton("取消", self)
        self.cancel_button.setObjectName('cancel')
        self.general_widget = QWidget(self)
        self.save_widget = QWidget(self)
        self.annotation_widget = QWidget(self)
        self.shortcut_widget = QWidget(self)

        self.quality_spinbox = QSpinBox(self.general_widget)
        self.quality_spinbox.setRange(1, 100)
        self.default_path_edit = QLineEdit(self.save_widget)
        self.save_name_edit = QLineEdit(self.save_widget)
        self.thin_width_edit = QLineEdit(self.annotation_widget)
        self.medium_width_edit = QLineEdit(self.annotation_widget)
        self.thick_width_edit = QLineEdit(self.annotation_widget)
        self.thin_preview = LinePreview()
        self.medium_preview = LinePreview()
        self.thick_preview = LinePreview()
        self.current_color = QColor()

        self.screenshot_key = ShortcutWidget()
        self.cancel_key = ShortcutWidget()
        self.copy_key = ShortcutWidget()
        self.save_key = ShortcutWidget()
        self.undo_key = ShortcutWidget()
        self.short_keys = [self.screenshot_key, self.cancel_key, self.copy_key, self.save_key, self.undo_key]
        self.dragging_threshold = 5  # 鼠标拖动的阈值
        self.setupUI()
        self.loadConfig()
        self.initEvents()

    def setupUI(self):
        self.base_layout.addWidget(self.tab_widget)
        self.base_layout.addLayout(self.createButtonLayout())

        self.setupGeneral()
        self.setupSave()
        self.setupAnnotation()
        self.setupShortcut()
        qss_file = open("./src/setting-style.qss", encoding='utf8')
        style_sheet = qss_file.read()
        self.setStyleSheet(style_sheet)
        self.setMinimumWidth(6 * self.tab_widget.width())


    def createButtonLayout(self):
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        return button_layout

    def setupGeneral(self):
        general_layout = QVBoxLayout(self.general_widget)
        self.auto_update_checkbox = QCheckBox("检查自动更新")
        self.auto_update_checkbox.setObjectName("autoUpdateCheckbox")
        general_layout.addWidget(self.auto_update_checkbox)
        self.startup_checkbox = QCheckBox("开机自启动")
        self.startup_checkbox.setObjectName("startupCheckbox")
        general_layout.addWidget(self.startup_checkbox)
        self.quality_spinbox.setObjectName("qualitySpinbox")
        general_layout.addWidget(QLabel("截图保存质量："))
        general_layout.addWidget(self.quality_spinbox)
        self.open_config_folder_button = QPushButton("打开所在配置文件夹")
        self.open_config_folder_button.setObjectName("openConfigFolderButton")
        general_layout.addWidget(self.open_config_folder_button)
        self.tab_widget.addTab(self.general_widget, "常规设置")

    def setupSave(self):
        self.silent_save = QCheckBox("是否静默保存")
        save_layout = QVBoxLayout(self.save_widget)
        save_layout.addWidget(self.silent_save)
        self.default_path_edit_label = QLabel("静默保存路径：")
        self.open_folder_button = QPushButton("···")
        self.open_folder_button.setObjectName('open_folder_button')
        self.select_save_layout = QHBoxLayout(self.save_widget)
        self.select_save_layout.addWidget(self.default_path_edit_label)
        self.select_save_layout.addWidget(self.default_path_edit)
        self.select_save_layout.addWidget(self.open_folder_button)
        save_layout.addLayout(self.select_save_layout)
        self.select_name_layout = QHBoxLayout(self.save_widget)
        self.select_name_layout.addWidget(QLabel("默认保存名字："))
        self.select_name_layout.addWidget(self.save_name_edit)
        save_layout.addLayout(self.select_name_layout)
        self.tab_widget.addTab(self.save_widget, "保存选项")

    def setupAnnotation(self):
        validator = QIntValidator()
        validator.setRange(1, 99)
        annotation_widget = self.annotation_widget
        annotation_layout = QVBoxLayout(annotation_widget)
        thin_width_layout = QHBoxLayout()
        thin_width_layout.addWidget(QLabel("细："))
        self.thin_width_edit.setValidator(validator)
        thin_width_layout.addWidget(self.thin_width_edit)
        thin_width_layout.addWidget(self.thin_preview)
        medium_width_layout = QHBoxLayout()
        medium_width_layout.addWidget(QLabel("中："))
        self.medium_width_edit.setValidator(validator)
        medium_width_layout.addWidget(self.medium_width_edit)
        medium_width_layout.addWidget(self.medium_preview)
        thick_width_layout = QHBoxLayout()
        thick_width_layout.addWidget(QLabel("粗："))
        self.thick_width_edit.setValidator(validator)
        thick_width_layout.addWidget(self.thick_width_edit)
        thick_width_layout.addWidget(self.thick_preview)
        annotation_layout.addLayout(thin_width_layout)
        annotation_layout.addLayout(medium_width_layout)
        annotation_layout.addLayout(thick_width_layout)
        self.set_default_color_button = QPushButton("线性默认颜色设置")
        self.set_default_color_button.setObjectName("openConfigFolderButton")
        annotation_layout.addWidget(self.set_default_color_button)
        self.tab_widget.addTab(annotation_widget, "标注设置")

    def setupShortcut(self):
        shortcut_layout = QVBoxLayout(self.shortcut_widget)
        screenshot_key_layout = QHBoxLayout()
        screenshot_key_layout.addWidget(QLabel("调用截图"))
        screenshot_key_layout.addWidget(self.screenshot_key)
        cancel_key_layout = QHBoxLayout()
        cancel_key_layout.addWidget(QLabel("取消截图"))
        cancel_key_layout.addWidget(self.cancel_key)
        copy_key_layout = QHBoxLayout()
        copy_key_layout.addWidget(QLabel("复制截图"))
        copy_key_layout.addWidget(self.copy_key)
        save_key_layout = QHBoxLayout()
        save_key_layout.addWidget(QLabel("保存截图"))
        save_key_layout.addWidget(self.save_key)
        undo_key_layout = QHBoxLayout()
        undo_key_layout.addWidget(QLabel("撤销截图"))
        undo_key_layout.addWidget(self.undo_key)
        shortcut_layout.addLayout(screenshot_key_layout)
        shortcut_layout.addLayout(cancel_key_layout)
        shortcut_layout.addLayout(copy_key_layout)
        shortcut_layout.addLayout(save_key_layout)
        shortcut_layout.addLayout(undo_key_layout)
        self.tab_widget.addTab(self.shortcut_widget, "热键设置")

    def initEvents(self):
        self.cancel_button.clicked.connect(self.hide)
        self.apply_button.clicked.connect(self.save_config)
        self.silent_save.stateChanged.connect(self.show_default_path)
        self.open_folder_button.clicked.connect(self.open_folder_dialog)
        self.tab_widget.tabBarClicked.connect(self.loadConfig)
        self.thin_width_edit.textChanged.connect(lambda: self.update_preview(self.thin_width_edit))
        self.medium_width_edit.textChanged.connect(lambda: self.update_preview(self.medium_width_edit))
        self.thick_width_edit.textChanged.connect(lambda: self.update_preview(self.thick_width_edit))
        self.set_default_color_button.clicked.connect(self.open_color_dialog)

    def update_preview(self, widgets: QLineEdit):
        if widgets == self.thin_width_edit:
            self.thin_preview.refresh(int(widgets.text()) if widgets.text() else 1, self.current_color)
        elif widgets == self.medium_width_edit:
            self.medium_preview.refresh(int(widgets.text()) if widgets.text() else 1, self.current_color)
        elif widgets == self.thick_width_edit:
            self.thick_preview.refresh(int(widgets.text()) if widgets.text() else 1, self.current_color)

    def hide(self) -> None:
        super().hide()

    def show_default_path(self):
        self.default_path_edit_label.setVisible(self.silent_save.isChecked())
        self.default_path_edit.setVisible(self.silent_save.isChecked())
        self.open_folder_button.setVisible(self.silent_save.isChecked())

    def loadConfig(self):
        self.title_bar.title_label.setText('软件设置')
        self.auto_update_checkbox.setChecked(self.settings.get('GeneralSettings', 'check_automatic_update') == 'True')
        self.startup_checkbox.setChecked(self.settings.get('GeneralSettings', 'is_startup') == 'True')
        self.quality_spinbox.setValue(int(self.settings.get('GeneralSettings', 'picture_quality')))
        self.silent_save.setChecked(self.settings.get('SaveSettings', 'is_silent_save') == 'True')
        self.default_path_edit.setText(self.settings.get('SaveSettings', 'default_path_edit'))
        self.save_name_edit.setText(self.settings.get('SaveSettings', 'save_name_edit'))
        self.show_default_path()
        self.thin_width_edit.setText(self.settings.get('AnnotationSettings', 'thin_width'))
        self.medium_width_edit.setText(self.settings.get('AnnotationSettings', 'medium_width'))
        self.thick_width_edit.setText(self.settings.get('AnnotationSettings', 'thick_width'))
        self.update_preview(self.thin_width_edit)
        self.update_preview(self.medium_width_edit)
        self.update_preview(self.thick_width_edit)
        self.current_color.setNamedColor(self.settings.get('AnnotationSettings', 'default_color'))
        self.setShortKeys()

    def setShortKeys(self):
        self.screenshot_key.setText(self.settings.get('ShortKeySettings', 'screenshot'))
        self.cancel_key.setText(self.settings.get('ShortKeySettings', 'cancel'))
        self.copy_key.setText(self.settings.get('ShortKeySettings', 'copy'))
        self.save_key.setText(self.settings.get('ShortKeySettings', 'save'))
        self.undo_key.setText(self.settings.get('ShortKeySettings', 'undo'))
        for key in self.short_keys:
            key.selected = False
            key.updateStyle()

    def save_config(self):
        self.settings.set('GeneralSettings', 'check_automatic_update',
                          'True' if self.auto_update_checkbox.isChecked() else 'False')
        self.settings.set('GeneralSettings', 'is_startup', 'True' if self.startup_checkbox.isChecked() else 'False')
        self.settings.set('GeneralSettings', 'picture_quality', str(self.quality_spinbox.value()))
        self.settings.set('SaveSettings', 'is_silent_save', 'True' if self.silent_save.isChecked() else 'False')
        self.settings.set('SaveSettings', 'default_path_edit',
                          self.default_path_edit.text() or str(self.settings.home_pictures))
        self.settings.set('SaveSettings', 'save_name_edit',
                          self.save_name_edit.text() or "hydra_{Y}{m}{d}_{h}{M}{S}.png")
        self.settings.set('AnnotationSettings', 'thin_width', self.thin_width_edit.text() or '1')
        self.settings.set('AnnotationSettings', 'medium_width', self.medium_width_edit.text() or '3')
        self.settings.set('AnnotationSettings', 'thick_width', self.thick_width_edit.text() or '6')
        self.settings.set('AnnotationSettings', 'default_color', self.current_color.name())
        self.settings.set('ShortKeySettings', 'screenshot', self.screenshot_key.text())
        self.settings.set('ShortKeySettings', 'cancel', self.cancel_key.text())
        self.settings.set('ShortKeySettings', 'copy', self.copy_key.text())
        self.settings.set('ShortKeySettings', 'save', self.save_key.text())
        self.settings.set('ShortKeySettings', 'undo', self.undo_key.text())
        self.settings.save_settings()
        self.title_bar.title_label.setText('软件设置-保存成功,请重启应用')

    def open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹路径")
        self.default_path_edit.setText(folder_path if folder_path else "")

    def open_color_dialog(self):
        color = QColorDialog.getColor(self.current_color, self, title='选择颜色')
        if color.isValid():
            self.current_color = color
            self.update_preview(self.thin_width_edit)
            self.update_preview(self.medium_width_edit)
            self.update_preview(self.thick_width_edit)


if __name__ == "__main__":
    app = QApplication([])
    window = SettingWindow()
    window.show()
    app.exec_()
