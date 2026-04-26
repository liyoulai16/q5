#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QListWidget, QListWidgetItem,
                             QSplitter, QMessageBox, QLabel)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

from modules.module_manager import ModuleManager
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
        
        splitter.setSizes([250, 950])
        
        main_layout.addWidget(splitter)
        
        self._create_status_bar()
    
    def _create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title_label = QLabel("工具套件")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        self.module_list = QListWidget()
        self.module_list.setIconSize(QSize(32, 32))
        self.module_list.setFont(QFont("Microsoft YaHei", 11))
        self.module_list.currentRowChanged.connect(self._on_module_selected)
        layout.addWidget(self.module_list)
        
        return panel
    
    def _create_status_bar(self):
        status_bar = self.statusBar()
        status_bar.showMessage("就绪")
    
    def _load_modules(self):
        modules = self.module_manager.get_available_modules()
        
        for module_id, module_info in modules.items():
            item = QListWidgetItem(module_info['name'])
            item.setData(Qt.ItemDataRole.UserRole, module_id)
            
            if 'icon' in module_info and module_info['icon']:
                try:
                    item.setIcon(QIcon(module_info['icon']))
                except:
                    pass
            
            self.module_list.addItem(item)
        
        if self.module_list.count() > 0:
            self.module_list.setCurrentRow(0)
    
    def _on_module_selected(self, index):
        if index < 0:
            return
        
        item = self.module_list.item(index)
        module_id = item.data(Qt.ItemDataRole.UserRole)
        
        module_widget = self._get_or_create_module_widget(module_id)
        if module_widget:
            self.content_stack.setCurrentWidget(module_widget)
            self.statusBar().showMessage(f"当前模块: {item.text()}")
    
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
