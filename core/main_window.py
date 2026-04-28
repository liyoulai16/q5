#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QTreeWidget, QTreeWidgetItem,
                             QSplitter, QLabel, QFrame, QHBoxLayout,
                             QPushButton)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QBrush

from modules.module_manager import ModuleManager, ModuleCategory
from modules.core_framework.core_framework_module import ThemeManager
from database.database_manager import DatabaseManager
from core.change_password_dialog import ChangePasswordDialog
from core.custom_dialogs import CustomMessageBox, CustomConfirmDialog


class MainWindow(QMainWindow):
    def __init__(self, current_user: str = None):
        super().__init__()
        self._current_user = current_user
        self.setWindowTitle("多功能桌面效率工具套件")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        self._theme_manager = ThemeManager()
        self._apply_theme()
        
        self.module_manager = ModuleManager()
        self.database_manager = DatabaseManager()
        
        self._init_ui()
        self._load_modules()
    
    def _apply_theme(self):
        """
        应用当前主题
        """
        stylesheet = self._theme_manager.generate_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        self.content_stack = QStackedWidget()
        splitter.addWidget(self.content_stack)
        
        splitter.setSizes([280, 920])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        self._create_status_bar()
    
    def _create_left_panel(self):
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1565C0;
                border: none;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 20, 15, 20)
        
        title_label = QLabel("工具套件")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("办公 · 生活 · 效率")
        subtitle_label.setFont(QFont("Microsoft YaHei", 10))
        subtitle_label.setStyleSheet("color: #BBDEFB;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)
        
        self.module_tree = QTreeWidget()
        self.module_tree.setHeaderHidden(True)
        self.module_tree.setIconSize(QSize(24, 24))
        self.module_tree.setFont(QFont("Microsoft YaHei", 11))
        self.module_tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background-color: #f8f9fa;
                outline: none;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565C0;
            }
            QTreeWidget::item:hover {
                background-color: #e9ecef;
            }
            QTreeWidget::branch {
                background-color: transparent;
            }
        """)
        self.module_tree.itemClicked.connect(self._on_module_item_clicked)
        self.module_tree.expandAll()
        
        layout.addWidget(self.module_tree, 1)
        
        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-top: 1px solid #dee2e6;
            }
        """)
        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(15, 10, 15, 10)
        user_layout.setSpacing(8)
        
        user_info_layout = QHBoxLayout()
        user_info_layout.setSpacing(10)
        
        user_icon_label = QLabel("👤")
        user_icon_label.setFont(QFont("Microsoft YaHei", 14))
        user_info_layout.addWidget(user_icon_label)
        
        user_text = f"当前用户: {self._current_user}" if self._current_user else "当前用户: 未登录"
        self._user_label = QLabel(user_text)
        self._user_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self._user_label.setStyleSheet("color: #333333;")
        user_info_layout.addWidget(self._user_label)
        user_info_layout.addStretch()
        
        user_layout.addLayout(user_info_layout)
        
        self._change_password_btn = QPushButton("🔑 修改密码")
        self._change_password_btn.setMinimumHeight(35)
        self._change_password_btn.setFont(QFont("Microsoft YaHei", 10))
        self._change_password_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._change_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self._change_password_btn.clicked.connect(self._on_change_password)
        
        user_layout.addWidget(self._change_password_btn)
        
        layout.addWidget(user_frame)
        
        return panel
    
    def _create_status_bar(self):
        status_bar = self.statusBar()
        status_bar.showMessage("就绪")
    
    def _load_modules(self):
        categories = self.module_manager.get_available_categories()
        self._category_items = {}
        self._module_items = {}
        
        for category in categories:
            category_name = ModuleCategory.CATEGORY_NAMES.get(category, category)
            category_icon = ModuleCategory.CATEGORY_ICONS.get(category, "📁")
            
            category_item = QTreeWidgetItem(self.module_tree)
            category_item.setText(0, f"  {category_icon}  {category_name}")
            category_item.setFont(0, QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
            category_item.setForeground(0, QBrush(QColor("#333333")))
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            
            self._category_items[category] = category_item
            
            modules = self.module_manager.get_modules_by_category(category)
            
            for module_id, module_info in modules.items():
                module_item = QTreeWidgetItem(category_item)
                module_item.setText(0, f"    {module_info['name']}")
                module_item.setData(0, Qt.ItemDataRole.UserRole, module_id)
                module_item.setData(0, Qt.ItemDataRole.UserRole + 1, "module")
                
                if 'icon' in module_info and module_info['icon']:
                    try:
                        module_item.setIcon(0, QIcon(module_info['icon']))
                    except:
                        pass
                
                self._module_items[module_id] = module_item
        
        if self._module_items:
            first_module_id = next(iter(self._module_items.keys()))
            first_module_item = self._module_items[first_module_id]
            self.module_tree.setCurrentItem(first_module_item)
            self._on_module_item_clicked(first_module_item, 0)
    
    def _on_module_item_clicked(self, item, column):
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_type != "module":
            return
        
        module_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not module_id:
            return
        
        module_widget = self._get_or_create_module_widget(module_id)
        if module_widget:
            self.content_stack.setCurrentWidget(module_widget)
            module_info = self.module_manager.get_available_modules().get(module_id, {})
            self.statusBar().showMessage(f"当前模块: {module_info.get('name', module_id)}")
    
    def _get_or_create_module_widget(self, module_id):
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if hasattr(widget, 'module_id') and widget.module_id == module_id:
                return widget
        
        module_instance = self.module_manager.load_module(module_id)
        if module_instance:
            module_widget = module_instance.get_widget()
            module_widget.module_id = module_id
            self.content_stack.addWidget(module_widget)
            return module_widget
        
        return None
    
    def _on_change_password(self):
        """
        修改密码按钮点击事件
        """
        if not self._current_user:
            CustomMessageBox.warning(self, "警告", "无法获取当前用户信息！")
            return
        
        dialog = ChangePasswordDialog(self._current_user, self)
        if dialog.exec() == ChangePasswordDialog.DialogCode.Accepted:
            CustomMessageBox.success(self, "提示", "密码修改成功，请重新登录。")
            self.close()
    
    def closeEvent(self, event):
        reply = CustomConfirmDialog.question(
            self, '确认退出',
            '确定要退出应用程序吗？',
            '退出', '取消', 'no'
        )
        
        if reply:
            self.database_manager.close()
            self.module_manager.unload_all_modules()
            event.accept()
        else:
            event.ignore()
