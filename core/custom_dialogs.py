#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义对话框
提供美观的信息、警告、确认、错误弹窗
"""

from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QSpacerItem,
                             QSizePolicy, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath, QPen, QBrush


class DialogType:
    """对话框类型常量"""
    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"
    SUCCESS = "success"


class CustomMessageBox(QDialog):
    """
    自定义消息框
    提供美观的信息、警告、错误、成功弹窗
    """
    
    DIALOG_STYLES = {
        DialogType.INFORMATION: {
            "icon": "ℹ️",
            "title": "信息",
            "color": "#2196F3",
            "bg_color": "#E3F2FD",
            "border_color": "#BBDEFB"
        },
        DialogType.WARNING: {
            "icon": "⚠️",
            "title": "警告",
            "color": "#FF9800",
            "bg_color": "#FFF3E0",
            "border_color": "#FFE0B2"
        },
        DialogType.ERROR: {
            "icon": "❌",
            "title": "错误",
            "color": "#F44336",
            "bg_color": "#FFEBEE",
            "border_color": "#FFCDD2"
        },
        DialogType.SUCCESS: {
            "icon": "✅",
            "title": "成功",
            "color": "#4CAF50",
            "bg_color": "#E8F5E9",
            "border_color": "#C8E6C9"
        },
        DialogType.QUESTION: {
            "icon": "❓",
            "title": "确认",
            "color": "#9C27B0",
            "bg_color": "#F3E5F5",
            "border_color": "#E1BEE7"
        }
    }
    
    def __init__(self, dialog_type: str, message: str, title: str = None, parent=None):
        super().__init__(parent)
        self._dialog_type = dialog_type
        self._message = message
        self._title = title or self.DIALOG_STYLES[dialog_type]["title"]
        self._result = None
        
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 220)
        self.setModal(True)
        
        self._init_ui()
    
    def _init_ui(self):
        style = self.DIALOG_STYLES[self._dialog_type]
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0)
        
        container = QFrame()
        container.setObjectName("dialogContainer")
        container.setStyleSheet(f"""
            #dialogContainer {{
                background-color: white;
                border-radius: 12px;
                border: 2px solid {style['border_color']};
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {style['bg_color']};
                border-radius: 8px;
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 12, 15, 12)
        header_layout.setSpacing(12)
        
        icon_label = QLabel(style["icon"])
        icon_label.setFont(QFont("Microsoft YaHei", 24))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(self._title)
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {style['color']};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        container_layout.addWidget(header_frame)
        
        message_frame = QFrame()
        message_layout = QVBoxLayout(message_frame)
        message_layout.setContentsMargins(10, 0, 10, 0)
        
        message_label = QLabel(self._message)
        message_label.setFont(QFont("Microsoft YaHei", 12))
        message_label.setStyleSheet("color: #333333;")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_layout.addWidget(message_label)
        
        container_layout.addWidget(message_frame, 1)
        
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        ok_btn = QPushButton("确 定")
        ok_btn.setMinimumHeight(40)
        ok_btn.setMinimumWidth(100)
        ok_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {style['color']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(style['color'], 20)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(style['color'], 30)};
            }}
        """)
        ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(ok_btn)
        
        container_layout.addWidget(button_frame)
        
        main_layout.addWidget(container)
    
    def _darken_color(self, color: str, amount: int) -> str:
        """将颜色加深指定的量"""
        color = color.lstrip('#')
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        r = max(0, r - amount)
        g = max(0, g - amount)
        b = max(0, b - amount)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _on_ok(self):
        self._result = True
        self.accept()
    
    def get_result(self):
        return self._result
    
    @staticmethod
    def information(parent, title, message):
        """显示信息对话框"""
        dialog = CustomMessageBox(DialogType.INFORMATION, message, title, parent)
        dialog.exec()
        return dialog.get_result()
    
    @staticmethod
    def warning(parent, title, message):
        """显示警告对话框"""
        dialog = CustomMessageBox(DialogType.WARNING, message, title, parent)
        dialog.exec()
        return dialog.get_result()
    
    @staticmethod
    def error(parent, title, message):
        """显示错误对话框"""
        dialog = CustomMessageBox(DialogType.ERROR, message, title, parent)
        dialog.exec()
        return dialog.get_result()
    
    @staticmethod
    def success(parent, title, message):
        """显示成功对话框"""
        dialog = CustomMessageBox(DialogType.SUCCESS, message, title, parent)
        dialog.exec()
        return dialog.get_result()


class CustomConfirmDialog(QDialog):
    """
    自定义确认对话框
    提供美观的是/否确认弹窗
    """
    
    def __init__(self, title: str, message: str, parent=None, 
                 yes_text: str = "是", no_text: str = "否",
                 default_button: str = "no"):
        super().__init__(parent)
        self._title = title
        self._message = message
        self._yes_text = yes_text
        self._no_text = no_text
        self._default_button = default_button
        self._result = False
        
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 240)
        self.setModal(True)
        
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0)
        
        container = QFrame()
        container.setObjectName("confirmContainer")
        container.setStyleSheet("""
            #confirmContainer {
                background-color: white;
                border-radius: 12px;
                border: 2px solid #E0E0E0;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(25, 20, 25, 20)
        container_layout.setSpacing(15)
        
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        icon_label = QLabel("❓")
        icon_label.setFont(QFont("Microsoft YaHei", 22))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(self._title)
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        container_layout.addWidget(header_frame)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #E0E0E0; background-color: #E0E0E0;")
        separator.setFixedHeight(1)
        container_layout.addWidget(separator)
        
        message_frame = QFrame()
        message_layout = QVBoxLayout(message_frame)
        message_layout.setContentsMargins(10, 5, 10, 5)
        
        message_label = QLabel(self._message)
        message_label.setFont(QFont("Microsoft YaHei", 12))
        message_label.setStyleSheet("color: #333333;")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_layout.addWidget(message_label)
        
        container_layout.addWidget(message_frame, 1)
        
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 5, 0, 0)
        button_layout.setSpacing(15)
        button_layout.addStretch()
        
        no_btn = QPushButton(self._no_text)
        no_btn.setMinimumHeight(42)
        no_btn.setMinimumWidth(110)
        no_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        no_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #666666;
                border: 1px solid #DDDDDD;
                border-radius: 8px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
                border-color: #CCCCCC;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
        """)
        no_btn.clicked.connect(self._on_no)
        button_layout.addWidget(no_btn)
        
        yes_btn = QPushButton(self._yes_text)
        yes_btn.setMinimumHeight(42)
        yes_btn.setMinimumWidth(110)
        yes_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
            }
        """)
        yes_btn.clicked.connect(self._on_yes)
        button_layout.addWidget(yes_btn)
        
        if self._default_button == "yes":
            yes_btn.setDefault(True)
            yes_btn.setFocus()
        else:
            no_btn.setDefault(True)
            no_btn.setFocus()
        
        container_layout.addWidget(button_frame)
        
        main_layout.addWidget(container)
    
    def _on_yes(self):
        self._result = True
        self.accept()
    
    def _on_no(self):
        self._result = False
        self.reject()
    
    def get_result(self):
        return self._result
    
    @staticmethod
    def question(parent, title, message, yes_text="是", no_text="否", default_button="no"):
        """显示确认对话框，返回True表示选择是，False表示选择否"""
        dialog = CustomConfirmDialog(title, message, parent, yes_text, no_text, default_button)
        result = dialog.exec()
        return dialog.get_result()


class CustomMessageDialog:
    """
    消息对话框工具类
    提供与QMessageBox兼容的接口，方便替换
    """
    
    class StandardButton:
        Yes = True
        No = False
    
    @staticmethod
    def information(parent, title, message, *args, **kwargs):
        """显示信息对话框"""
        CustomMessageBox.information(parent, title, message)
        return True
    
    @staticmethod
    def warning(parent, title, message, *args, **kwargs):
        """显示警告对话框"""
        CustomMessageBox.warning(parent, title, message)
        return True
    
    @staticmethod
    def critical(parent, title, message, *args, **kwargs):
        """显示错误对话框"""
        CustomMessageBox.error(parent, title, message)
        return True
    
    @staticmethod
    def question(parent, title, message, buttons=None, defaultButton=None):
        """显示确认对话框"""
        from PyQt6.QtWidgets import QMessageBox
        yes_text = "是"
        no_text = "否"
        default = "no"
        
        if defaultButton == QMessageBox.StandardButton.Yes:
            default = "yes"
        
        return CustomConfirmDialog.question(parent, title, message, yes_text, no_text, default)
