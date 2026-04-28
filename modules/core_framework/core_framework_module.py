#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心框架模块
提供主题切换等核心功能
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QButtonGroup, QRadioButton,
                             QGroupBox, QFormLayout, QComboBox, QCheckBox,
                             QSlider, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QColor

from modules.module_manager import BaseModule, ModuleCategory
from core.custom_dialogs import CustomMessageBox


class ThemeManager:
    """
    主题管理器
    管理应用程序的主题切换和样式应用
    """
    
    LIGHT_THEME = "light"
    DARK_THEME = "dark"
    BLUE_THEME = "blue"
    GREEN_THEME = "green"
    
    THEMES = {
        LIGHT_THEME: {
            "name": "浅色主题",
            "icon": "☀️",
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
        },
        DARK_THEME: {
            "name": "深色主题",
            "icon": "🌙",
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
        },
        BLUE_THEME: {
            "name": "海洋蓝主题",
            "icon": "🌊",
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
        },
        GREEN_THEME: {
            "name": "森林绿主题",
            "icon": "🌲",
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
    }
    
    _instance = None
    _current_theme = LIGHT_THEME
    _theme_changed = pyqtSignal(str)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_theme_setting()
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._settings = QSettings("ToolSuite", "ThemeSettings")
    
    def _load_theme_setting(self):
        """加载保存的主题设置"""
        settings = QSettings("ToolSuite", "ThemeSettings")
        saved_theme = settings.value("current_theme", self.LIGHT_THEME)
        if saved_theme in self.THEMES:
            self._current_theme = saved_theme
    
    def get_current_theme(self) -> str:
        """获取当前主题"""
        return self._current_theme
    
    def get_theme_info(self, theme_name: str = None) -> dict:
        """获取主题信息"""
        if theme_name is None:
            theme_name = self._current_theme
        return self.THEMES.get(theme_name, self.THEMES[self.LIGHT_THEME])
    
    def get_all_themes(self) -> dict:
        """获取所有可用主题"""
        return self.THEMES.copy()
    
    def set_theme(self, theme_name: str) -> bool:
        """设置主题"""
        if theme_name not in self.THEMES:
            return False
        
        self._current_theme = theme_name
        self._settings.setValue("current_theme", theme_name)
        return True
    
    def generate_stylesheet(self, theme_name: str = None) -> str:
        """生成主题样式表"""
        theme = self.get_theme_info(theme_name)
        
        stylesheet = f"""
        /* 全局样式 */
        QWidget {{
            background-color: {theme['background']};
            color: {theme['text_primary']};
            font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
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
        card = QFrame()
        card.setObjectName(f"themeCard_{theme_id}")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        card_style = f"""
        #themeCard_{theme_id} {{
            background-color: {theme_info['secondary_bg']};
            border: 3px solid {'#1565C0' if is_selected else theme_info['border']};
            border-radius: 12px;
            padding: 15px;
        }}
        #themeCard_{theme_id}:hover {{
            border-color: {theme_info['primary_color']};
        }}
        """
        card.setStyleSheet(card_style)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        icon_label = QLabel(theme_info['icon'])
        icon_label.setFont(QFont("Microsoft YaHei", 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        name_label = QLabel(theme_info['name'])
        name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {theme_info['text_primary']};")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        preview_frame = QFrame()
        preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme_info['primary_color']};
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
        radio_btn.setStyleSheet(f"color: {theme_info['text_primary']};")
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
        
        font_size_label = QLabel("字体大小:")
        font_size_label.setFont(QFont("Microsoft YaHei", 11))
        
        font_size_layout = QHBoxLayout()
        self._font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self._font_size_slider.setMinimum(10)
        self._font_size_slider.setMaximum(18)
        self._font_size_slider.setValue(12)
        self._font_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._font_size_slider.setTickInterval(2)
        self._font_size_slider.setMinimumWidth(200)
        
        self._font_size_value = QLabel("12")
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
        
        layout.addRow(compact_mode_label, self._compact_mode_check)
        
        animations_label = QLabel("动画效果:")
        animations_label.setFont(QFont("Microsoft YaHei", 11))
        
        self._animations_check = QCheckBox("启用UI动画效果")
        self._animations_check.setFont(QFont("Microsoft YaHei", 10))
        self._animations_check.setChecked(True)
        
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
        
        theme_id = selected_button.property("theme_id")
        if self._theme_manager.set_theme(theme_id):
            theme_info = self._theme_manager.get_theme_info(theme_id)
            CustomMessageBox.success(
                None, 
                "主题已应用", 
                f"成功切换到 {theme_info['name']}！\n\n请重启应用程序以完全应用主题效果。"
            )
        else:
            CustomMessageBox.error(None, "错误", "主题切换失败！")
