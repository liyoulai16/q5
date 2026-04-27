#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码管理器模块
生活工具分类下的密码管理功能
"""

import random
import string
from datetime import datetime
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QGroupBox, QScrollArea,
                             QFrame, QMessageBox, QTabWidget, QListWidget, 
                             QListWidgetItem, QTextEdit, QSplitter, QCheckBox,
                             QSpacerItem, QSizePolicy, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QClipboard, QGuiApplication

from modules.module_manager import BaseModule, ModuleCategory
from database.database_manager import DatabaseManager


PASSWORD_CATEGORIES = [
    ("全部", "全部"),
    ("⭐ 收藏", "收藏"),
    ("社交账号", "📱"),
    ("工作邮箱", "📧"),
    ("金融服务", "💰"),
    ("购物网站", "🛒"),
    ("游戏账号", "🎮"),
    ("其他", "📁"),
]

FAVORITES_CATEGORY = "⭐ 收藏"


class PasswordStrengthChecker:
    """密码强度检查器"""
    
    @staticmethod
    def check_strength(password: str) -> tuple:
        """
        检查密码强度
        返回 (强度等级: 0-4, 颜色代码, 描述文本)
        """
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        
        if any(c.islower() for c in password):
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in string.punctuation for c in password):
            score += 1
        
        if score <= 2:
            return (0, "#f44336", "弱")
        elif score <= 3:
            return (1, "#FF9800", "中等")
        elif score <= 4:
            return (2, "#FFC107", "强")
        else:
            return (3, "#4CAF50", "非常强")


class PasswordCard(QFrame):
    """密码卡片组件"""
    
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    copy_clicked = pyqtSignal(str)
    favorite_clicked = pyqtSignal(int, bool)
    
    def __init__(self, password_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.password_data = password_data
        self._fav_btn = None
        self._init_ui()
    
    def get_password_id(self) -> int:
        return self.password_data.get('id', 0)
    
    def update_favorite_status(self, is_favorite: bool):
        """更新收藏状态，只更新按钮显示"""
        self.password_data['is_favorite'] = 1 if is_favorite else 0
        if self._fav_btn:
            self._fav_btn.setText("⭐" if is_favorite else "☆")
    
    def _init_ui(self):
        self.setMinimumHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            QFrame:hover {
                border: 1px solid #1565C0;
                background-color: #FAFAFA;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)
        
        is_favorite = self.password_data.get('is_favorite', 0) == 1
        self._fav_btn = QPushButton("⭐" if is_favorite else "☆")
        self._fav_btn.setMaximumWidth(35)
        self._fav_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #FFF8E1;
                border-radius: 4px;
            }
        """)
        self._fav_btn.clicked.connect(self._on_fav_clicked)
        layout.addWidget(self._fav_btn)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        category = self.password_data.get('category', '其他')
        category_icon = "📁"
        for cat, icon in PASSWORD_CATEGORIES[2:]:
            if cat == category:
                category_icon = icon
                break
        
        cat_label = QLabel(category_icon)
        cat_label.setFont(QFont("Microsoft YaHei", 14))
        title_layout.addWidget(cat_label)
        
        title_label = QLabel(self.password_data.get('title', '未命名'))
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        info_layout.addLayout(title_layout)
        
        username = self.password_data.get('username', '')
        if username:
            user_label = QLabel(f"👤 {username}")
            user_label.setFont(QFont("Microsoft YaHei", 10))
            user_label.setStyleSheet("color: #666666;")
            info_layout.addWidget(user_label)
        
        website = self.password_data.get('website', '')
        if website:
            web_label = QLabel(f"🌐 {website[:50]}{'...' if len(website) > 50 else ''}")
            web_label.setFont(QFont("Microsoft YaHei", 9))
            web_label.setStyleSheet("color: #999999;")
            info_layout.addWidget(web_label)
        
        layout.addLayout(info_layout, 1)
        
        action_layout = QVBoxLayout()
        action_layout.setSpacing(8)
        
        copy_btn = QPushButton("📋 复制")
        copy_btn.setMinimumWidth(70)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        copy_btn.clicked.connect(lambda: self.copy_clicked.emit(self.password_data.get('password', '')))
        action_layout.addWidget(copy_btn)
        
        btn_row_layout = QHBoxLayout()
        btn_row_layout.setSpacing(5)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setMaximumWidth(32)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 4px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.password_data['id']))
        btn_row_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setMaximumWidth(32)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 4px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.password_data['id']))
        btn_row_layout.addWidget(delete_btn)
        
        action_layout.addLayout(btn_row_layout)
        
        layout.addLayout(action_layout)
    
    def _on_fav_clicked(self):
        """收藏按钮点击"""
        current_is_favorite = self.password_data.get('is_favorite', 0) == 1
        new_is_favorite = not current_is_favorite
        self.favorite_clicked.emit(self.password_data['id'], new_is_favorite)


class PasswordEditDialog(QDialog):
    """密码编辑对话框"""
    
    def __init__(self, password_data: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        self.password_data = password_data or {}
        self._init_ui()
    
    def _init_ui(self):
        is_edit = bool(self.password_data)
        self.setWindowTitle("编辑密码" if is_edit else "添加新密码")
        self.setMinimumSize(500, 550)
        self.setStyleSheet("""
            QDialog {
                background-color: #fafafa;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(15)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)
        title_label = QLabel("标题 *")
        title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333;")
        title_layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setMinimumHeight(40)
        self.title_input.setFont(QFont("Microsoft YaHei", 11))
        self.title_input.setPlaceholderText("例如：GitHub 账号")
        self.title_input.setText(self.password_data.get('title', ''))
        self.title_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
            }
        """)
        title_layout.addWidget(self.title_input)
        form_layout.addLayout(title_layout)
        
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(15)
        
        username_layout = QVBoxLayout()
        username_layout.setSpacing(5)
        user_label = QLabel("用户名/邮箱")
        user_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        user_label.setStyleSheet("color: #333333;")
        username_layout.addWidget(user_label)
        
        self.username_input = QLineEdit()
        self.username_input.setMinimumHeight(40)
        self.username_input.setFont(QFont("Microsoft YaHei", 11))
        self.username_input.setPlaceholderText("用户名或邮箱")
        self.username_input.setText(self.password_data.get('username', ''))
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
            }
        """)
        username_layout.addWidget(self.username_input)
        row1_layout.addLayout(username_layout, 1)
        
        category_layout = QVBoxLayout()
        category_layout.setSpacing(5)
        cat_label = QLabel("分类")
        cat_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        cat_label.setStyleSheet("color: #333333;")
        category_layout.addWidget(cat_label)
        
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(40)
        self.category_combo.setFont(QFont("Microsoft YaHei", 11))
        for cat, icon in PASSWORD_CATEGORIES[1:]:
            self.category_combo.addItem(f"{icon} {cat}", cat)
        
        current_category = self.password_data.get('category', '其他')
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == current_category:
                self.category_combo.setCurrentIndex(i)
                break
        
        self.category_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #1565C0;
            }
        """)
        category_layout.addWidget(self.category_combo)
        row1_layout.addLayout(category_layout, 1)
        
        form_layout.addLayout(row1_layout)
        
        password_layout = QVBoxLayout()
        password_layout.setSpacing(5)
        pwd_label = QLabel("密码 *")
        pwd_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        pwd_label.setStyleSheet("color: #333333;")
        password_layout.addWidget(pwd_label)
        
        pwd_input_layout = QHBoxLayout()
        pwd_input_layout.setSpacing(10)
        
        self.password_input = QLineEdit()
        self.password_input.setMinimumHeight(40)
        self.password_input.setFont(QFont("Microsoft YaHei", 11))
        self.password_input.setPlaceholderText("输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setText(self.password_data.get('password', ''))
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
            }
        """)
        self.password_input.textChanged.connect(self._on_password_changed)
        pwd_input_layout.addWidget(self.password_input, 1)
        
        self.show_pwd_btn = QPushButton("👁️")
        self.show_pwd_btn.setMaximumWidth(45)
        self.show_pwd_btn.setMinimumHeight(40)
        self.show_pwd_btn.setCheckable(True)
        self.show_pwd_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #1565C0;
                color: white;
            }
        """)
        self.show_pwd_btn.clicked.connect(self._toggle_password_visibility)
        pwd_input_layout.addWidget(self.show_pwd_btn)
        
        gen_btn = QPushButton("🎲 生成")
        gen_btn.setMinimumHeight(40)
        gen_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        gen_btn.clicked.connect(self._generate_password)
        pwd_input_layout.addWidget(gen_btn)
        
        password_layout.addLayout(pwd_input_layout)
        
        self.strength_label = QLabel("")
        self.strength_label.setFont(QFont("Microsoft YaHei", 9))
        password_layout.addWidget(self.strength_label)
        
        form_layout.addLayout(password_layout)
        
        website_layout = QVBoxLayout()
        website_layout.setSpacing(5)
        web_label = QLabel("网站/URL")
        web_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        web_label.setStyleSheet("color: #333333;")
        website_layout.addWidget(web_label)
        
        self.website_input = QLineEdit()
        self.website_input.setMinimumHeight(40)
        self.website_input.setFont(QFont("Microsoft YaHei", 11))
        self.website_input.setPlaceholderText("例如：https://github.com")
        self.website_input.setText(self.password_data.get('website', ''))
        self.website_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
            }
        """)
        website_layout.addWidget(self.website_input)
        form_layout.addLayout(website_layout)
        
        notes_layout = QVBoxLayout()
        notes_layout.setSpacing(5)
        notes_label = QLabel("备注")
        notes_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        notes_label.setStyleSheet("color: #333333;")
        notes_layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMinimumHeight(80)
        self.notes_input.setFont(QFont("Microsoft YaHei", 11))
        self.notes_input.setPlaceholderText("添加备注信息...")
        self.notes_input.setText(self.password_data.get('notes', ''))
        self.notes_input.setStyleSheet("""
            QTextEdit {
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #1565C0;
            }
        """)
        notes_layout.addWidget(self.notes_input)
        form_layout.addLayout(notes_layout)
        
        layout.addLayout(form_layout)
        
        self.favorite_check = QCheckBox("⭐ 添加到收藏")
        self.favorite_check.setFont(QFont("Microsoft YaHei", 10))
        self.favorite_check.setChecked(self.password_data.get('is_favorite', 0) == 1)
        layout.addWidget(self.favorite_check)
        
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        button_box.button(QDialogButtonBox.StandardButton.Ok).setMinimumHeight(40)
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setMinimumHeight(40)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setFont(QFont("Microsoft YaHei", 11))
        button_box.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 30px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self._on_password_changed(self.password_input.text())
    
    def _toggle_password_visibility(self):
        """切换密码可见性"""
        if self.show_pwd_btn.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_pwd_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_pwd_btn.setText("👁️")
    
    def _on_password_changed(self, text: str):
        """密码改变时更新强度显示"""
        if not text:
            self.strength_label.setText("")
            return
        
        level, color, desc = PasswordStrengthChecker.check_strength(text)
        self.strength_label.setText(f"密码强度: <font color='{color}'><b>{desc}</b></font>")
    
    def _generate_password(self):
        """生成随机密码"""
        length = 16
        chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        password = ''.join(random.choice(chars) for _ in range(length))
        self.password_input.setText(password)
    
    def _on_accept(self):
        """确认按钮点击"""
        title = self.title_input.text().strip()
        password = self.password_input.text()
        
        if not title:
            QMessageBox.warning(self, "警告", "请输入标题！")
            self.title_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "警告", "请输入密码！")
            self.password_input.setFocus()
            return
        
        self.accept()
    
    def get_password_data(self) -> Dict[str, Any]:
        """获取密码数据"""
        return {
            'title': self.title_input.text().strip(),
            'username': self.username_input.text().strip(),
            'password': self.password_input.text(),
            'website': self.website_input.text().strip(),
            'category': self.category_combo.currentData(),
            'notes': self.notes_input.toPlainText().strip(),
            'is_favorite': 1 if self.favorite_check.isChecked() else 0,
        }


class PasswordManagerMainWidget(QWidget):
    """密码管理器主界面组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = DatabaseManager()
        self._current_category = "全部"
        self._search_text = ""
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🔐 密码管理器")
        title_label.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setMinimumWidth(250)
        self.search_input.setMinimumHeight(40)
        self.search_input.setFont(QFont("Microsoft YaHei", 11))
        self.search_input.setPlaceholderText("🔍 搜索标题、用户名、网站...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 20px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        header_layout.addWidget(self.search_input)
        
        self.add_btn = QPushButton("➕ 添加密码")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 25px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
        """)
        self.add_btn.clicked.connect(self._on_add_password)
        header_layout.addWidget(self.add_btn)
        
        main_layout.addLayout(header_layout)
        
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        filter_label = QLabel("分类:")
        filter_label.setFont(QFont("Microsoft YaHei", 10))
        filter_label.setStyleSheet("color: #666666;")
        filter_layout.addWidget(filter_label)
        
        self.category_buttons = []
        for category, icon in PASSWORD_CATEGORIES:
            btn = QPushButton(f"{icon} {category}")
            btn.setMinimumHeight(35)
            btn.setFont(QFont("Microsoft YaHei", 10))
            btn.setCheckable(True)
            btn.setChecked(category == "全部")
            btn.setProperty("category", category)
            
            if category == "全部":
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1565C0;
                        color: white;
                        border: none;
                        padding: 5px 15px;
                        border-radius: 17px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f5f5f5;
                        color: #666666;
                        border: 1px solid #ddd;
                        padding: 5px 15px;
                        border-radius: 17px;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                    QPushButton:checked {
                        background-color: #1565C0;
                        color: white;
                        border: none;
                    }
                """)
            
            btn.clicked.connect(lambda checked, c=category: self._on_category_changed(c))
            self.category_buttons.append(btn)
            filter_layout.addWidget(btn)
        
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        
        self.stats_label = QLabel("")
        self.stats_label.setFont(QFont("Microsoft YaHei", 10))
        self.stats_label.setStyleSheet("color: #666666;")
        main_layout.addWidget(self.stats_label)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)
        
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(5, 5, 5, 5)
        self.container_layout.setSpacing(12)
        
        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area, 1)
        
        self._load_passwords()
    
    def _on_category_changed(self, category: str):
        """分类改变"""
        self._current_category = category
        
        for btn in self.category_buttons:
            btn_cat = btn.property("category")
            if btn_cat == category:
                btn.setChecked(True)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1565C0;
                        color: white;
                        border: none;
                        padding: 5px 15px;
                        border-radius: 17px;
                    }
                """)
            else:
                btn.setChecked(False)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f5f5f5;
                        color: #666666;
                        border: 1px solid #ddd;
                        padding: 5px 15px;
                        border-radius: 17px;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                """)
        
        self._load_passwords()
    
    def _on_search_changed(self, text: str):
        """搜索改变"""
        self._search_text = text.strip().lower()
        self._load_passwords()
    
    def _load_passwords(self):
        """加载密码列表"""
        for i in reversed(range(self.container_layout.count())):
            item = self.container_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        query = "SELECT * FROM passwords WHERE 1=1"
        params = []
        
        if self._current_category == FAVORITES_CATEGORY:
            query += " AND is_favorite = 1"
        elif self._current_category != "全部":
            query += " AND category = ?"
            params.append(self._current_category)
        
        if self._search_text:
            query += " AND (title LIKE ? OR username LIKE ? OR website LIKE ? OR notes LIKE ?)"
            search_param = f"%{self._search_text}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        query += " ORDER BY is_favorite DESC, updated_at DESC"
        
        passwords = self._db.query_all(query, tuple(params))
        
        if not passwords:
            no_data_label = QLabel("暂无密码记录\n\n点击「添加密码」按钮开始管理您的密码")
            no_data_label.setFont(QFont("Microsoft YaHei", 14))
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_label.setStyleSheet("color: #999999; padding: 80px;")
            self.container_layout.addWidget(no_data_label)
            self.stats_label.setText(f"共 0 条记录")
            return
        
        for pwd_data in passwords:
            card = PasswordCard(pwd_data)
            card.edit_clicked.connect(self._on_edit_password)
            card.delete_clicked.connect(self._on_delete_password)
            card.copy_clicked.connect(self._on_copy_password)
            card.favorite_clicked.connect(self._on_toggle_favorite)
            self.container_layout.addWidget(card)
        
        self.container_layout.addStretch()
        
        total_count = self._db.query_scalar("SELECT COUNT(*) FROM passwords")
        self.stats_label.setText(f"共 {len(passwords)} 条记录 (总计 {total_count} 条)")
    
    def _on_add_password(self):
        """添加密码"""
        dialog = PasswordEditDialog(parent=self)
        if dialog.exec() == PasswordEditDialog.DialogCode.Accepted:
            data = dialog.get_password_data()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['created_at'] = now
            data['updated_at'] = now
            
            pwd_id = self._db.insert('passwords', data)
            if pwd_id > 0:
                QMessageBox.information(self, "成功", "密码已添加！")
                self._load_passwords()
    
    def _on_edit_password(self, pwd_id: int):
        """编辑密码"""
        pwd_data = self._db.query_one(
            "SELECT * FROM passwords WHERE id = ?",
            (pwd_id,)
        )
        
        if not pwd_data:
            QMessageBox.warning(self, "警告", "密码记录不存在！")
            return
        
        dialog = PasswordEditDialog(pwd_data, parent=self)
        if dialog.exec() == PasswordEditDialog.DialogCode.Accepted:
            data = dialog.get_password_data()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['updated_at'] = now
            
            affected = self._db.update(
                'passwords',
                data,
                'id = ?',
                (pwd_id,)
            )
            
            if affected > 0:
                QMessageBox.information(self, "成功", "密码已更新！")
                self._load_passwords()
    
    def _on_delete_password(self, pwd_id: int):
        """删除密码"""
        pwd_data = self._db.query_one(
            "SELECT title FROM passwords WHERE id = ?",
            (pwd_id,)
        )
        
        if not pwd_data:
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除密码 \"{pwd_data['title']}\" 吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            affected = self._db.delete('passwords', 'id = ?', (pwd_id,))
            if affected > 0:
                QMessageBox.information(self, "成功", "密码已删除！")
                self._load_passwords()
    
    def _on_copy_password(self, password: str):
        """复制密码到剪贴板"""
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(password, QClipboard.Mode.Clipboard)
            QMessageBox.information(self, "提示", "密码已复制到剪贴板！")
    
    def _on_toggle_favorite(self, pwd_id: int, new_is_favorite: bool):
        """切换收藏状态 - 只更新数据库和当前卡片显示，不重新排序"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_favorite_value = 1 if new_is_favorite else 0
        
        self._db.update(
            'passwords',
            {'is_favorite': new_favorite_value, 'updated_at': now},
            'id = ?',
            (pwd_id,)
        )
        
        for i in range(self.container_layout.count()):
            item = self.container_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'get_password_id') and widget.get_password_id() == pwd_id:
                    widget.update_favorite_status(new_is_favorite)
                    break


class PasswordManagerModule(BaseModule):
    """
    密码管理器模块
    提供密码存储和管理功能
    """
    
    @property
    def module_id(self) -> str:
        return "password_manager"
    
    @property
    def name(self) -> str:
        return "密码管理器"
    
    @property
    def description(self) -> str:
        return "安全管理您的各种账号密码，支持分类、搜索和收藏"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def category(self) -> str:
        return ModuleCategory.LIFE_TOOLS
    
    @property
    def author(self) -> str:
        return "System"
    
    def _on_load(self) -> None:
        """
        模块加载时的初始化
        """
        self._db = DatabaseManager()
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        pass
    
    def _create_widget(self) -> QWidget:
        """
        创建密码管理器的主界面
        """
        return PasswordManagerMainWidget()
