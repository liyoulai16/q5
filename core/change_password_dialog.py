#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改密码对话框
提供用户修改密码的界面和功能
"""

from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox,
                             QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap

from database.database_manager import DatabaseManager


class ChangePasswordDialog(QDialog):
    """
    修改密码对话框
    """
    
    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self._username = username
        self._db = DatabaseManager()
        
        self.setWindowTitle("修改密码")
        self.setFixedSize(420, 480)
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
        header_layout.setContentsMargins(30, 20, 30, 20)
        header_layout.setSpacing(8)
        
        icon_label = QLabel("🔑")
        icon_label.setFont(QFont("Microsoft YaHei", 36))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        title_label = QLabel("修改密码")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        user_label = QLabel(f"当前用户: {self._username}")
        user_label.setFont(QFont("Microsoft YaHei", 10))
        user_label.setStyleSheet("color: #BBDEFB;")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(user_label)
        
        main_layout.addWidget(header_frame)
        
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(40, 25, 40, 25)
        content_layout.setSpacing(35)
        
        old_password_layout = QVBoxLayout()
        old_password_layout.setSpacing(15)
        
        old_password_label = QLabel("旧密码")
        old_password_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        old_password_label.setStyleSheet("color: #333333;")
        old_password_layout.addWidget(old_password_label)
        
        self.old_password_input = QLineEdit()
        self.old_password_input.setMinimumHeight(45)
        self.old_password_input.setFont(QFont("Microsoft YaHei", 12))
        self.old_password_input.setPlaceholderText("请输入旧密码")
        self.old_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_password_input.setStyleSheet("""
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
        self.old_password_input.returnPressed.connect(self._on_change_password)
        old_password_layout.addWidget(self.old_password_input)
        
        content_layout.addLayout(old_password_layout)
        
        new_password_layout = QVBoxLayout()
        new_password_layout.setSpacing(15)
        
        new_password_label = QLabel("新密码")
        new_password_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        new_password_label.setStyleSheet("color: #333333;")
        new_password_layout.addWidget(new_password_label)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setMinimumHeight(45)
        self.new_password_input.setFont(QFont("Microsoft YaHei", 12))
        self.new_password_input.setPlaceholderText("请输入新密码")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setStyleSheet("""
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
        self.new_password_input.returnPressed.connect(self._on_change_password)
        new_password_layout.addWidget(self.new_password_input)
        
        content_layout.addLayout(new_password_layout)
        
        confirm_password_layout = QVBoxLayout()
        confirm_password_layout.setSpacing(15)
        
        confirm_password_label = QLabel("确认新密码")
        confirm_password_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        confirm_password_label.setStyleSheet("color: #333333;")
        confirm_password_layout.addWidget(confirm_password_label)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setMinimumHeight(45)
        self.confirm_password_input.setFont(QFont("Microsoft YaHei", 12))
        self.confirm_password_input.setPlaceholderText("请再次输入新密码")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setStyleSheet("""
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
        self.confirm_password_input.returnPressed.connect(self._on_change_password)
        confirm_password_layout.addWidget(self.confirm_password_input)
        
        content_layout.addLayout(confirm_password_layout)
        
        content_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumHeight(45)
        cancel_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #666666;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #bdbdbd;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        self.confirm_btn = QPushButton("确认修改")
        self.confirm_btn.setMinimumHeight(45)
        self.confirm_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setStyleSheet("""
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
        self.confirm_btn.clicked.connect(self._on_change_password)
        
        btn_layout.addWidget(cancel_btn, 1)
        btn_layout.addWidget(self.confirm_btn, 1)
        
        content_layout.addLayout(btn_layout)
        
        content_layout.addStretch()
        
        main_layout.addWidget(content_frame, 1)
        
        self.old_password_input.setFocus()
    
    def _on_change_password(self):
        """
        确认修改密码按钮点击事件
        """
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not old_password:
            QMessageBox.warning(self, "警告", "请输入旧密码！")
            self.old_password_input.setFocus()
            return
        
        if not new_password:
            QMessageBox.warning(self, "警告", "请输入新密码！")
            self.new_password_input.setFocus()
            return
        
        if len(new_password) < 4:
            QMessageBox.warning(self, "警告", "新密码长度不能少于4位！")
            self.new_password_input.setFocus()
            return
        
        if not confirm_password:
            QMessageBox.warning(self, "警告", "请确认新密码！")
            self.confirm_password_input.setFocus()
            return
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "警告", "两次输入的新密码不一致！")
            self.confirm_password_input.clear()
            self.confirm_password_input.setFocus()
            return
        
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setText("修改中...")
        
        try:
            if self._db.change_password(self._username, old_password, new_password):
                QMessageBox.information(self, "修改成功", "密码修改成功！请使用新密码登录。")
                self.accept()
            else:
                QMessageBox.warning(self, "修改失败", "旧密码错误，请重新输入！")
                self.old_password_input.clear()
                self.old_password_input.setFocus()
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"修改密码时发生错误: {str(e)}")
        
        finally:
            self.confirm_btn.setEnabled(True)
            self.confirm_btn.setText("确认修改")
