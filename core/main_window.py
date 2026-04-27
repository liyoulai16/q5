#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QTreeWidget, QTreeWidgetItem,
                             QSplitter, QMessageBox, QLabel, QFrame, QHBoxLayout)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QBrush

from modules.module_manager import ModuleManager, ModuleCategory
from database.database_manager import DatabaseManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多功能桌面效率工具套件")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        self.module_manager = ModuleManager()
        self.database_manager = DatabaseManager()
        
        self._init_ui()
        self._load_modules()
    
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
    
    def closeEvent(self, event):
        reply = QMessageBox.question(self, '确认退出',
                                     '确定要退出应用程序吗？',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.database_manager.close()
            self.module_manager.unload_all_modules()
            event.accept()
        else:
            event.ignore()
