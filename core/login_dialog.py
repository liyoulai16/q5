#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录对话框
提供用户登录界面和验证功能
"""

from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox,
                             QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap

from database.database_manager import DatabaseManager


class LoginDialog(QDialog):
    """
    登录对话框
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = DatabaseManager()
        self._authenticated = False
        self._current_user = None
        
        self.setWindowTitle("用户登录")
        self.setFixedSize(420, 520)
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._init_ui()
    
    def _init_ui(self):
        """
        初始化UI界面
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1565C0, stop:1 #1976D2);
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 25, 30, 25)
        header_layout.setSpacing(8)
        
        icon_label = QLabel("🔐")
        icon_label.setFont(QFont("Microsoft YaHei", 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        title_label = QLabel("多功能工具套件")
        title_label.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("请登录以继续使用")
        subtitle_label.setFont(QFont("Microsoft YaHei", 11))
        subtitle_label.setStyleSheet("color: #BBDEFB;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        main_layout.addWidget(header_frame)
        
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(40, 20, 40, 20)
        content_layout.setSpacing(15)
        
        username_layout = QVBoxLayout()
        username_layout.setSpacing(8)
        
        username_label = QLabel("用户名")
        username_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        username_label.setStyleSheet("color: #333333;")
        username_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setMinimumHeight(45)
        self.username_input.setFont(QFont("Microsoft YaHei", 12))
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setText("user")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #FAFAFA;
            }
            QLineEdit:focus {
                border-color: #1565C0;
                background-color: white;
            }
        """)
        self.username_input.returnPressed.connect(self._on_login)
        username_layout.addWidget(self.username_input)
        
        content_layout.addLayout(username_layout)
        
        password_layout = QVBoxLayout()
        password_layout.setSpacing(8)
        
        password_label = QLabel("密码")
        password_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        password_label.setStyleSheet("color: #333333;")
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setMinimumHeight(45)
        self.password_input.setFont(QFont("Microsoft YaHei", 12))
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #FAFAFA;
            }
            QLineEdit:focus {
                border-color: #1565C0;
                background-color: white;
            }
        """)
        self.password_input.returnPressed.connect(self._on_login)
        password_layout.addWidget(self.password_input)
        
        content_layout.addLayout(password_layout)
        
        content_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        self.login_btn = QPushButton("登 录")
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.login_btn.clicked.connect(self._on_login)
        content_layout.addWidget(self.login_btn)
        
        content_layout.addSpacerItem(QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        info_label = QLabel("默认账号: user / 123456")
        info_label.setFont(QFont("Microsoft YaHei", 9))
        info_label.setStyleSheet("color: #999999;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(info_label)
        
        content_layout.addStretch()
        
        main_layout.addWidget(content_frame, 1)
        
        self.username_input.setFocus()
    
    def _on_login(self):
        """
        登录按钮点击事件
        """
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username:
            QMessageBox.warning(self, "警告", "请输入用户名！")
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "警告", "请输入密码！")
            self.password_input.setFocus()
            return
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText("登录中...")
        
        try:
            if self._db.verify_password(username, password):
                self._db.update_last_login(username)
                self._authenticated = True
                self._current_user = username
                
                QMessageBox.information(self, "登录成功", f"欢迎回来，{username}！")
                self.accept()
            else:
                QMessageBox.warning(self, "登录失败", "用户名或密码错误！")
                self.password_input.clear()
                self.password_input.setFocus()
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录时发生错误: {str(e)}")
        
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("登 录")
    
    def is_authenticated(self) -> bool:
        """
        检查是否已通过身份验证
        """
        return self._authenticated
    
    def get_current_user(self) -> str:
        """
        获取当前登录的用户名
        """
        return self._current_user
