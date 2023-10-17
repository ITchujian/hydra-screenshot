import os
import configparser
from pathlib import Path


class Settings:
    def __init__(self, defaults=None, filename='settings.ini'):
        self.version_number = 1
        self.version = '1.0 alpha'
        self.config = configparser.ConfigParser(defaults=defaults)
        self.home = Path.home()
        self.home_pictures = self.home / "Pictures"
        self.fmt_dict = {
            '{Y}': '%Y',
            '{m}': '%m',
            '{d}': '%d',
            '{H}': '%H',
            '{M}': '%M',
            '{S}': '%S'
        }

        # 检查配置文件是否存在
        self.filename = filename
        if not os.path.exists(self.filename):
            self.create_default_settings()

        self.config.read(self.filename)

    def get(self, section, option, fallback=None):
        """获取配置项"""
        return self.config.get(section, option, fallback=fallback)

    def set(self, section, option, value):
        """设置配置项"""
        self.config.set(section, option, value)

    def create_default_settings(self):
        """创建默认配置文件并设置默认值"""
        self.config['SoftwareConfig'] = {
            'exe_icon': './src/exe.ico',
            'logo': './src/logo.png',
        }
        self.config['GeneralSettings'] = {
            'check_automatic_update': 'True',
            'is_startup': 'False',
            'picture_quality': '100',
        }
        self.config['SaveSettings'] = {
            'is_silent_save': 'False',
            'default_path_edit': str(self.home_pictures),
            'save_name_edit': 'hydra_{Y}{m}{d}_{H}{M}{S}.png',
        }
        self.config['AnnotationSettings'] = {
            'thin_width': '2',
            'medium_width': '4',
            'thick_width': '6',
            'default_color': '#FF0000'
        }
        self.config['ShortKeySettings'] = {
            'screenshot': 'ctrl+`',
            'cancel': 'esc',
            'copy': 'ctrl+c',
            'save': 'ctrl+s',
            'undo': 'ctrl+z',
        }
        self.config['IconPaths'] = {
            'rectangle_icon': './src/rectangle.png',
            'ellipse_icon': './src/ellipse.png',
            'arrow_icon': './src/arrow.png',
            'graffiti_icon': './src/graffiti.png',
            'number_icon': './src/number.png',
            'text_icon': './src/text.png',
            'undo_icon': './src/undo.png',
            'tongs_icon': './src/tongs.png',
            'long_icon': './src/long.png',
            'save_icon': './src/save.png',
            'to_top_icon': './src/to-top.png',
            'cancel_icon': './src/cancel.png',
            'ok_icon': './src/ok.png',
            'font_setting_icon': './src/font-setting.png',
            'copy_icon': './src/copy.png',
            'close_icon': './src/close.png',
        }
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)

    def save_settings(self):
        """将路径信息保存到配置文件"""
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)

    def module_parser(self, module: str):
        result = module
        for k, v in self.fmt_dict.items():
            result = result.replace(k, v)
        return result
