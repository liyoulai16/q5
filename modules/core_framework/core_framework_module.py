#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心框架模块
提供主题切换等核心功能
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QButtonGroup, QRadioButton,
                             QGroupBox, QFormLayout, QComboBox, QCheckBox,
                             QSlider, QSpinBox, QColorDialog, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QColor, QPalette

from modules.module_manager import BaseModule, ModuleCategory
from core.custom_dialogs import CustomMessageBox


class ThemeManager:
    """
    主题管理器
    管理应用程序的主题切换和样式应用
    支持多种预定义主题和自定义主题
    """
    
    LIGHT_THEME = "light"
    DARK_THEME = "dark"
    BLUE_THEME = "blue"
    GREEN_THEME = "green"
    PURPLE_THEME = "purple"
    ORANGE_THEME = "orange"
    PINK_THEME = "pink"
    TEAL_THEME = "teal"
    HIGH_CONTRAST_THEME = "high_contrast"
    CUSTOM_THEME = "custom"
    
    THEMES = {
        LIGHT_THEME: {
            "name": "浅色主题",
            "icon": "☀️",
            "is_custom": False,
            "colors": {
                "primary_color": "#1565C0",
                "primary_light": "#1976D2",
                "primary_dark": "#0D47A1",
                "background": "#FFFFFF",
                "secondary_bg": "#F8F9FA",
                "tertiary_bg": "#F0F0F0",
                "text_primary": "#333333",
                "text_secondary": "#666666",
                "text_hint": "#999999",
                "border": "#E0E0E0",
                "border_light": "#EEEEEE",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336",
                "info": "#2196F3"
            }
        },
        DARK_THEME: {
            "name": "深色主题",
            "icon": "🌙",
            "is_custom": False,
            "colors": {
                "primary_color": "#64B5F6",
                "primary_light": "#90CAF9",
                "primary_dark": "#42A5F5",
                "background": "#1E1E1E",
                "secondary_bg": "#252526",
                "tertiary_bg": "#2D2D2D",
                "text_primary": "#E0E0E0",
                "text_secondary": "#A0A0A0",
                "text_hint": "#666666",
                "border": "#3C3C3C",
                "border_light": "#333333",
                "success": "#81C784",
                "warning": "#FFB74D",
                "error": "#E57373",
                "info": "#64B5F6"
            }
        },
        BLUE_THEME: {
            "name": "海洋蓝主题",
            "icon": "🌊",
            "is_custom": False,
            "colors": {
                "primary_color": "#0288D1",
                "primary_light": "#03A9F4",
                "primary_dark": "#01579B",
                "background": "#E1F5FE",
                "secondary_bg": "#B3E5FC",
                "tertiary_bg": "#81D4FA",
                "text_primary": "#01579B",
                "text_secondary": "#0277BD",
                "text_hint": "#0288D1",
                "border": "#4FC3F7",
                "border_light": "#81D4FA",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336",
                "info": "#0288D1"
            }
        },
        GREEN_THEME: {
            "name": "森林绿主题",
            "icon": "🌲",
            "is_custom": False,
            "colors": {
                "primary_color": "#2E7D32",
                "primary_light": "#388E3C",
                "primary_dark": "#1B5E20",
                "background": "#E8F5E9",
                "secondary_bg": "#C8E6C9",
                "tertiary_bg": "#A5D6A7",
                "text_primary": "#1B5E20",
                "text_secondary": "#2E7D32",
                "text_hint": "#388E3C",
                "border": "#81C784",
                "border_light": "#A5D6A7",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336",
                "info": "#2196F3"
            }
        },
        PURPLE_THEME: {
            "name": "优雅紫主题",
            "icon": "💜",
            "is_custom": False,
            "colors": {
                "primary_color": "#7B1FA2",
                "primary_light": "#9C27B0",
                "primary_dark": "#4A148C",
                "background": "#F3E5F5",
                "secondary_bg": "#E1BEE7",
                "tertiary_bg": "#CE93D8",
                "text_primary": "#4A148C",
                "text_secondary": "#7B1FA2",
                "text_hint": "#9C27B0",
                "border": "#BA68C8",
                "border_light": "#CE93D8",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336",
                "info": "#2196F3"
            }
        },
        ORANGE_THEME: {
            "name": "活力橙主题",
            "icon": "🍊",
            "is_custom": False,
            "colors": {
                "primary_color": "#E65100",
                "primary_light": "#F57C00",
                "primary_dark": "#BF360C",
                "background": "#FFF3E0",
                "secondary_bg": "#FFE0B2",
                "tertiary_bg": "#FFCC80",
                "text_primary": "#BF360C",
                "text_secondary": "#E65100",
                "text_hint": "#F57C00",
                "border": "#FFB74D",
                "border_light": "#FFCC80",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336",
                "info": "#2196F3"
            }
        },
        PINK_THEME: {
            "name": "浪漫粉主题",
            "icon": "🌸",
            "is_custom": False,
            "colors": {
                "primary_color": "#C2185B",
                "primary_light": "#D81B60",
                "primary_dark": "#880E4F",
                "background": "#FCE4EC",
                "secondary_bg": "#F8BBD9",
                "tertiary_bg": "#F48FB1",
                "text_primary": "#880E4F",
                "text_secondary": "#C2185B",
                "text_hint": "#D81B60",
                "border": "#F48FB1",
                "border_light": "#F8BBD9",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336",
                "info": "#2196F3"
            }
        },
        TEAL_THEME: {
            "name": "清新青主题",
            "icon": "💎",
            "is_custom": False,
            "colors": {
                "primary_color": "#00796B",
                "primary_light": "#009688",
                "primary_dark": "#004D40",
                "background": "#E0F2F1",
                "secondary_bg": "#B2DFDB",
                "tertiary_bg": "#80CBC4",
                "text_primary": "#004D40",
                "text_secondary": "#00796B",
                "text_hint": "#009688",
                "border": "#4DB6AC",
                "border_light": "#80CBC4",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336",
                "info": "#2196F3"
            }
        },
        HIGH_CONTRAST_THEME: {
            "name": "高对比度主题",
            "icon": "🔲",
            "is_custom": False,
            "colors": {
                "primary_color": "#FFFFFF",
                "primary_light": "#FFFFFF",
                "primary_dark": "#CCCCCC",
                "background": "#000000",
                "secondary_bg": "#111111",
                "tertiary_bg": "#222222",
                "text_primary": "#FFFFFF",
                "text_secondary": "#FFFFFF",
                "text_hint": "#FFFFFF",
                "border": "#FFFFFF",
                "border_light": "#FFFFFF",
                "success": "#00FF00",
                "warning": "#FFFF00",
                "error": "#FF0000",
                "info": "#00FFFF"
            }
        }
    }
    
    _instance = None
    _current_theme = LIGHT_THEME
    _theme_changed = pyqtSignal(str)
    _custom_colors = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._settings = QSettings("ToolSuite", "ThemeSettings")
        self._load_all_settings()
        self._theme_callbacks: list = []
    
    def _load_all_settings(self):
        """加载所有主题相关设置"""
        saved_theme = self._settings.value("current_theme", self.LIGHT_THEME)
        if saved_theme in self.THEMES or saved_theme == self.CUSTOM_THEME:
            self._current_theme = saved_theme
        
        self._font_size = self._settings.value("font_size", 12, type=int)
        self._compact_mode = self._settings.value("compact_mode", False, type=bool)
        self._animations_enabled = self._settings.value("animations_enabled", True, type=bool)
        self._font_family = self._settings.value("font_family", "Microsoft YaHei")
        
        custom_colors_str = self._settings.value("custom_colors")
        if custom_colors_str:
            try:
                import json
                self._custom_colors = json.loads(custom_colors_str)
            except:
                self._custom_colors = None
    
    def get_current_theme(self) -> str:
        """获取当前主题"""
        return self._current_theme
    
    def get_theme_info(self, theme_name: str = None) -> dict:
        """获取主题信息"""
        if theme_name is None:
            theme_name = self._current_theme
        
        if theme_name == self.CUSTOM_THEME and self._custom_colors:
            return {
                "name": "自定义主题",
                "icon": "🎨",
                "is_custom": True,
                "colors": self._custom_colors
            }
        
        theme = self.THEMES.get(theme_name)
        if theme:
            return theme
        
        return self.THEMES[self.LIGHT_THEME]
    
    def get_all_themes(self) -> dict:
        """获取所有可用主题"""
        result = self.THEMES.copy()
        if self._custom_colors:
            result[self.CUSTOM_THEME] = {
                "name": "自定义主题",
                "icon": "🎨",
                "is_custom": True,
                "colors": self._custom_colors
            }
        return result
    
    def set_theme(self, theme_name: str) -> bool:
        """设置主题"""
        if theme_name not in self.THEMES and theme_name != self.CUSTOM_THEME:
            return False
        
        if theme_name == self.CUSTOM_THEME and not self._custom_colors:
            return False
        
        self._current_theme = theme_name
        self._settings.setValue("current_theme", theme_name)
        self._notify_theme_changed()
        return True
    
    def set_custom_colors(self, colors: dict) -> bool:
        """设置自定义主题颜色"""
        required_keys = [
            "primary_color", "primary_light", "primary_dark",
            "background", "secondary_bg", "tertiary_bg",
            "text_primary", "text_secondary", "text_hint",
            "border", "border_light",
            "success", "warning", "error", "info"
        ]
        
        for key in required_keys:
            if key not in colors:
                return False
        
        self._custom_colors = colors.copy()
        
        import json
        self._settings.setValue("custom_colors", json.dumps(colors))
        return True
    
    def get_custom_colors(self) -> dict:
        """获取自定义主题颜色"""
        if self._custom_colors:
            return self._custom_colors.copy()
        return {}
    
    def has_custom_theme(self) -> bool:
        """检查是否有自定义主题"""
        return self._custom_colors is not None
    
    def get_appearance_settings(self) -> dict:
        """获取外观设置"""
        return {
            "font_size": self._font_size,
            "compact_mode": self._compact_mode,
            "animations_enabled": self._animations_enabled,
            "font_family": self._font_family
        }
    
    def set_appearance_settings(self, settings: dict) -> bool:
        """设置外观设置"""
        if "font_size" in settings:
            self._font_size = settings["font_size"]
            self._settings.setValue("font_size", self._font_size)
        
        if "compact_mode" in settings:
            self._compact_mode = settings["compact_mode"]
            self._settings.setValue("compact_mode", self._compact_mode)
        
        if "animations_enabled" in settings:
            self._animations_enabled = settings["animations_enabled"]
            self._settings.setValue("animations_enabled", self._animations_enabled)
        
        if "font_family" in settings:
            self._font_family = settings["font_family"]
            self._settings.setValue("font_family", self._font_family)
        
        self._notify_theme_changed()
        return True
    
    def _notify_theme_changed(self):
        """通知主题变化"""
        for callback in self._theme_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"主题回调执行失败: {e}")
    
    def add_theme_change_callback(self, callback):
        """添加主题变化回调"""
        if callback not in self._theme_callbacks:
            self._theme_callbacks.append(callback)
    
    def remove_theme_change_callback(self, callback):
        """移除主题变化回调"""
        if callback in self._theme_callbacks:
            self._theme_callbacks.remove(callback)
    
    def generate_stylesheet(self, theme_name: str = None) -> str:
        """生成主题样式表"""
        theme_info = self.get_theme_info(theme_name)
        theme = theme_info.get('colors', theme_info)
        
        appearance = self.get_appearance_settings()
        font_size = appearance.get('font_size', 12)
        font_family = appearance.get('font_family', 'Microsoft YaHei')
        compact_mode = appearance.get('compact_mode', False)
        
        padding_small = "4px" if compact_mode else "8px"
        padding_medium = "6px" if compact_mode else "10px"
        padding_large = "8px 16px" if compact_mode else "10px 20px"
        
        stylesheet = f"""
        /* 全局样式 */
        QWidget {{
            background-color: {theme['background']};
            color: {theme['text_primary']};
            font-family: "{font_family}", "Segoe UI", Arial, sans-serif;
            font-size: {font_size}px;
        }}
        
        /* 主窗口和容器 */
        QMainWindow {{
            background-color: {theme['background']};
        }}
        
        QFrame {{
            background-color: {theme['background']};
            border: none;
        }}
        
        /* 标签 */
        QLabel {{
            background-color: transparent;
            color: {theme['text_primary']};
        }}
        
        /* 按钮 */
        QPushButton {{
            background-color: {theme['primary_color']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 13px;
        }}
        
        QPushButton:hover {{
            background-color: {theme['primary_light']};
        }}
        
        QPushButton:pressed {{
            background-color: {theme['primary_dark']};
        }}
        
        QPushButton:disabled {{
            background-color: {theme['border']};
            color: {theme['text_hint']};
        }}
        
        /* 次要按钮样式 */
        QPushButton[secondary="true"] {{
            background-color: {theme['secondary_bg']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
        }}
        
        QPushButton[secondary="true"]:hover {{
            background-color: {theme['tertiary_bg']};
            border-color: {theme['text_secondary']};
        }}
        
        /* 输入框 */
        QLineEdit {{
            background-color: {theme['secondary_bg']};
            color: {theme['text_primary']};
            border: 2px solid {theme['border']};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
        }}
        
        QLineEdit:focus {{
            border-color: {theme['primary_color']};
            background-color: {theme['background']};
        }}
        
        QLineEdit:disabled {{
            background-color: {theme['tertiary_bg']};
            color: {theme['text_hint']};
        }}
        
        /* 文本编辑框 */
        QTextEdit {{
            background-color: {theme['secondary_bg']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            padding: 4px;
        }}
        
        QTextEdit:focus {{
            border-color: {theme['primary_color']};
            background-color: {theme['background']};
        }}
        
        /* 列表视图 */
        QListWidget {{
            background-color: {theme['secondary_bg']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
        }}
        
        QListWidget::item {{
            padding: 6px;
            border-bottom: 1px solid {theme['border_light']};
        }}
        
        QListWidget::item:selected {{
            background-color: {theme['primary_color']};
            color: white;
        }}
        
        QListWidget::item:hover {{
            background-color: {theme['tertiary_bg']};
        }}
        
        /* 树视图 */
        QTreeWidget {{
            background-color: {theme['secondary_bg']};
            color: {theme['text_primary']};
            border: none;
            outline: none;
        }}
        
        QTreeWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {theme['border_light']};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {theme['primary_color']};
            color: white;
        }}
        
        QTreeWidget::item:hover {{
            background-color: {theme['tertiary_bg']};
        }}
        
        /* 组合框 */
        QComboBox {{
            background-color: {theme['secondary_bg']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            padding: 6px 12px;
            min-width: 100px;
        }}
        
        QComboBox:hover {{
            border-color: {theme['primary_color']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {theme['background']};
            color: {theme['text_primary']};
            selection-background-color: {theme['primary_color']};
            selection-color: white;
        }}
        
        /* 复选框 */
        QCheckBox {{
            background-color: transparent;
            color: {theme['text_primary']};
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid {theme['border']};
            background-color: {theme['secondary_bg']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {theme['primary_color']};
            border-color: {theme['primary_color']};
        }}
        
        /* 单选按钮 */
        QRadioButton {{
            background-color: transparent;
            color: {theme['text_primary']};
            spacing: 8px;
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 2px solid {theme['border']};
            background-color: {theme['secondary_bg']};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {theme['primary_color']};
            border-color: {theme['primary_color']};
        }}
        
        /* 分组框 */
        QGroupBox {{
            background-color: {theme['secondary_bg']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 8px;
            margin-top: 16px;
            padding-top: 10px;
            font-weight: bold;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 16px;
            top: -8px;
            padding: 0 8px;
            background-color: {theme['secondary_bg']};
        }}
        
        /* 滚动条 */
        QScrollBar:vertical {{
            background-color: {theme['secondary_bg']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {theme['border']};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {theme['text_secondary']};
        }}
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {theme['secondary_bg']};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {theme['border']};
            border-radius: 6px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {theme['text_secondary']};
        }}
        
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* 滑块 */
        QSlider::groove:horizontal {{
            background-color: {theme['border']};
            height: 6px;
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background-color: {theme['primary_color']};
            width: 18px;
            height: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background-color: {theme['primary_light']};
        }}
        
        /* 进度条 */
        QProgressBar {{
            background-color: {theme['secondary_bg']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {theme['primary_color']};
            border-radius: 3px;
        }}
        
        /* 微调框 */
        QSpinBox, QDoubleSpinBox {{
            background-color: {theme['secondary_bg']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            padding: 4px 8px;
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {theme['primary_color']};
        }}
        
        /* 标签页 */
        QTabWidget::pane {{
            border: 1px solid {theme['border']};
            border-radius: 4px;
            background-color: {theme['secondary_bg']};
        }}
        
        QTabBar::tab {{
            background-color: {theme['tertiary_bg']};
            color: {theme['text_secondary']};
            border: 1px solid {theme['border']};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 8px 16px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {theme['secondary_bg']};
            color: {theme['primary_color']};
            border-bottom: 2px solid {theme['primary_color']};
        }}
        
        QTabBar::tab:hover {{
            background-color: {theme['secondary_bg']};
        }}
        
        /* 状态栏 */
        QStatusBar {{
            background-color: {theme['tertiary_bg']};
            color: {theme['text_secondary']};
            border-top: 1px solid {theme['border']};
        }}
        
        /* 工具提示 */
        QToolTip {{
            background-color: {theme['text_primary']};
            color: {theme['background']};
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
        }}
        """
        
        return stylesheet


class CoreFrameworkModule(BaseModule):
    """
    核心框架模块
    提供主题切换等核心功能
    """
    
    @property
    def module_id(self) -> str:
        return "core_framework"
    
    @property
    def name(self) -> str:
        return "主题设置"
    
    @property
    def description(self) -> str:
        return "提供主题切换、系统设置等核心功能"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def category(self) -> str:
        return ModuleCategory.CORE_FRAMEWORK
    
    @property
    def author(self) -> str:
        return "System"
    
    def _on_load(self) -> None:
        """
        模块加载时的初始化
        """
        self._theme_manager = ThemeManager()
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        pass
    
    def _create_widget(self) -> QWidget:
        """
        创建核心框架的主界面
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565C0, stop:1 #1976D2);
                border-radius: 12px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 25, 30, 25)
        header_layout.setSpacing(10)
        
        title_label = QLabel("⚙️ 核心框架设置")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        desc_label = QLabel("管理应用程序的主题、外观和系统设置")
        desc_label.setFont(QFont("Microsoft YaHei", 11))
        desc_label.setStyleSheet("color: #BBDEFB;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(desc_label)
        
        main_layout.addWidget(header_frame)
        
        theme_group = self._create_theme_group()
        main_layout.addWidget(theme_group)
        
        appearance_group = self._create_appearance_group()
        main_layout.addWidget(appearance_group)
        
        main_layout.addStretch()
        
        return widget
    
    def _create_theme_group(self) -> QGroupBox:
        """
        创建主题设置组
        """
        group = QGroupBox("🎨 主题设置")
        group.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(15)
        
        desc_label = QLabel("选择您喜欢的主题风格，应用程序将立即切换到所选主题。")
        desc_label.setFont(QFont("Microsoft YaHei", 10))
        desc_label.setStyleSheet("color: #666666;")
        layout.addWidget(desc_label)
        
        self._theme_button_group = QButtonGroup(group)
        themes_layout = QHBoxLayout()
        themes_layout.setSpacing(15)
        
        current_theme = self._theme_manager.get_current_theme()
        themes = self._theme_manager.get_all_themes()
        
        for theme_id, theme_info in themes.items():
            theme_card = self._create_theme_card(theme_id, theme_info, theme_id == current_theme)
            themes_layout.addWidget(theme_card)
        
        themes_layout.addStretch()
        layout.addLayout(themes_layout)
        
        apply_btn = QPushButton("✨ 应用主题")
        apply_btn.setMinimumHeight(45)
        apply_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._on_apply_theme)
        layout.addWidget(apply_btn)
        
        return group
    
    def _create_theme_card(self, theme_id: str, theme_info: dict, is_selected: bool) -> QFrame:
        """
        创建主题卡片
        """
        colors = theme_info.get('colors', theme_info)
        
        card = QFrame()
        card.setObjectName(f"themeCard_{theme_id}")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        card_style = f"""
        #themeCard_{theme_id} {{
            background-color: {colors['secondary_bg']};
            border: 3px solid {'#1565C0' if is_selected else colors['border']};
            border-radius: 12px;
            padding: 15px;
        }}
        #themeCard_{theme_id}:hover {{
            border-color: {colors['primary_color']};
        }}
        """
        card.setStyleSheet(card_style)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        icon_label = QLabel(theme_info.get('icon', '🎨'))
        icon_label.setFont(QFont("Microsoft YaHei", 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        name_label = QLabel(theme_info.get('name', theme_id))
        name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {colors['text_primary']};")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        preview_frame = QFrame()
        preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['primary_color']};
                border-radius: 6px;
                border: none;
            }}
        """)
        preview_frame.setMinimumHeight(30)
        preview_frame.setMaximumHeight(30)
        layout.addWidget(preview_frame)
        
        radio_btn = QRadioButton("选择")
        radio_btn.setFont(QFont("Microsoft YaHei", 10))
        radio_btn.setChecked(is_selected)
        radio_btn.setProperty("theme_id", theme_id)
        radio_btn.setStyleSheet(f"color: {colors['text_primary']};")
        self._theme_button_group.addButton(radio_btn)
        layout.addWidget(radio_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return card
    
    def _create_appearance_group(self) -> QGroupBox:
        """
        创建外观设置组
        """
        group = QGroupBox("👁️ 外观设置")
        group.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        
        layout = QFormLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(15)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        appearance_settings = self._theme_manager.get_appearance_settings()
        
        font_size_label = QLabel("字体大小:")
        font_size_label.setFont(QFont("Microsoft YaHei", 11))
        
        font_size_layout = QHBoxLayout()
        self._font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self._font_size_slider.setMinimum(10)
        self._font_size_slider.setMaximum(18)
        self._font_size_slider.setValue(appearance_settings.get('font_size', 12))
        self._font_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._font_size_slider.setTickInterval(2)
        self._font_size_slider.setMinimumWidth(200)
        
        self._font_size_value = QLabel(str(appearance_settings.get('font_size', 12)))
        self._font_size_value.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._font_size_value.setMinimumWidth(30)
        
        self._font_size_slider.valueChanged.connect(
            lambda v: self._font_size_value.setText(str(v))
        )
        
        font_size_layout.addWidget(self._font_size_slider)
        font_size_layout.addWidget(self._font_size_value)
        font_size_layout.addStretch()
        
        layout.addRow(font_size_label, font_size_layout)
        
        compact_mode_label = QLabel("紧凑模式:")
        compact_mode_label.setFont(QFont("Microsoft YaHei", 11))
        
        self._compact_mode_check = QCheckBox("使用更紧凑的布局")
        self._compact_mode_check.setFont(QFont("Microsoft YaHei", 10))
        self._compact_mode_check.setChecked(appearance_settings.get('compact_mode', False))
        
        layout.addRow(compact_mode_label, self._compact_mode_check)
        
        animations_label = QLabel("动画效果:")
        animations_label.setFont(QFont("Microsoft YaHei", 11))
        
        self._animations_check = QCheckBox("启用UI动画效果")
        self._animations_check.setFont(QFont("Microsoft YaHei", 10))
        self._animations_check.setChecked(appearance_settings.get('animations_enabled', True))
        
        layout.addRow(animations_label, self._animations_check)
        
        return group
    
    def _on_apply_theme(self):
        """
        应用主题按钮点击事件
        """
        selected_button = self._theme_button_group.checkedButton()
        if not selected_button:
            CustomMessageBox.warning(None, "提示", "请先选择一个主题！")
            return
        
        appearance_settings = {
            "font_size": self._font_size_slider.value(),
            "compact_mode": self._compact_mode_check.isChecked(),
            "animations_enabled": self._animations_check.isChecked()
        }
        self._theme_manager.set_appearance_settings(appearance_settings)
        
        theme_id = selected_button.property("theme_id")
        if self._theme_manager.set_theme(theme_id):
            theme_info = self._theme_manager.get_theme_info(theme_id)
            CustomMessageBox.success(
                None, 
                "主题已应用", 
                f"成功切换到 {theme_info['name']}！\n\n外观设置已保存。"
            )
        else:
            CustomMessageBox.error(None, "错误", "主题切换失败！")
