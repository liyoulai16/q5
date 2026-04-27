#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF工具模块
提供PDF文件的转换、编辑、合并、拆分等功能
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
                             QLabel, QSplitter, QGroupBox, QFormLayout, QSpinBox,
                             QLineEdit, QComboBox, QCheckBox, QTextEdit, QInputDialog,
                             QTabWidget, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont, QPixmap, QImage

from modules.module_manager import BaseModule, ModuleCategory
from database.database_manager import DatabaseManager

try:
    from pypdf import PdfReader, PdfWriter
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


class PdfToolModule(BaseModule):
    """
    PDF工具模块
    提供PDF文件的转换、编辑、合并、拆分等功能
    """
    
    @property
    def module_id(self) -> str:
        return "pdf_tool"
    
    @property
    def name(self) -> str:
        return "PDF工具"
    
    @property
    def description(self) -> str:
        return "PDF文件处理工具，支持合并、拆分、旋转、加密、转换等功能"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def author(self) -> str:
        return "System"
    
    def _on_load(self) -> None:
        """
        模块加载时的初始化
        """
        self._db = DatabaseManager()
        self._create_pdf_history_table()
        self._current_pdf_files: List[Dict[str, Any]] = []
        self._current_selected_pdf: Optional[Dict[str, Any]] = None
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        self._current_pdf_files = []
        self._current_selected_pdf = None
    
    def _create_pdf_history_table(self):
        """
        创建PDF操作历史记录表
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS pdf_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL,
            source_file TEXT,
            target_file TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self._db.execute(create_table_sql)
    
    def _create_widget(self) -> QWidget:
        """
        创建PDF工具的主界面
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)
        
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        file_list_panel = self._create_file_list_panel()
        content_splitter.addWidget(file_list_panel)
        
        operation_panel = self._create_operation_panel()
        content_splitter.addWidget(operation_panel)
        
        content_splitter.setSizes([350, 850])
        
        main_layout.addWidget(content_splitter, 1)
        
        self._check_dependencies()
        
        return widget
    
    def _check_dependencies(self):
        """
        检查依赖库是否安装
        """
        missing_libs = []
        if not PYPDF_AVAILABLE:
            missing_libs.append("pypdf")
        if not PDF2IMAGE_AVAILABLE:
            missing_libs.append("pdf2image")
        
        if missing_libs:
            QMessageBox.warning(
                None, "缺少依赖",
                f"以下依赖库未安装:\n{', '.join(missing_libs)}\n\n"
                f"请运行: pip install {' '.join(missing_libs)}\n\n"
                f"注意: PDF转图片功能还需要安装poppler工具。"
            )
    
    def _create_toolbar(self) -> QWidget:
        """
        创建工具栏
        """
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        add_btn = QPushButton("添加PDF文件")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        add_btn.clicked.connect(self._on_add_pdf)
        layout.addWidget(add_btn)
        
        remove_btn = QPushButton("移除选中")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        remove_btn.clicked.connect(self._on_remove_pdf)
        layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("清空列表")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #EF6C00;
            }
        """)
        clear_btn.clicked.connect(self._on_clear_list)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        
        history_btn = QPushButton("操作历史")
        history_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #6A1B9A;
            }
        """)
        history_btn.clicked.connect(self._on_show_history)
        layout.addWidget(history_btn)
        
        return toolbar
    
    def _create_file_list_panel(self) -> QWidget:
        """
        创建PDF文件列表面板
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        
        title_label = QLabel("PDF文件列表")
        title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333; padding: 2px;")
        layout.addWidget(title_label)
        
        self.pdf_list = QListWidget()
        self.pdf_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 2px;
                padding: 0px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565C0;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.pdf_list.currentRowChanged.connect(self._on_pdf_selected)
        layout.addWidget(self.pdf_list, 1)
        
        info_group = QGroupBox("文件信息")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 2px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
            }
        """)
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setSpacing(4)
        
        self.file_info_label = QLabel("未选择文件")
        self.file_info_label.setStyleSheet("color: #666;")
        self.file_info_label.setWordWrap(True)
        info_layout.addWidget(self.file_info_label)
        
        layout.addWidget(info_group)
        
        return panel
    
    def _create_operation_panel(self) -> QWidget:
        """
        创建操作面板（使用标签页）
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        
        title_label = QLabel("PDF操作工具")
        title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333; padding: 2px;")
        layout.addWidget(title_label)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 2px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #1565C0;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e0e0e0;
            }
        """)
        
        self.tab_widget.addTab(self._create_merge_tab(), "合并PDF")
        self.tab_widget.addTab(self._create_split_tab(), "拆分PDF")
        self.tab_widget.addTab(self._create_rotate_tab(), "旋转页面")
        self.tab_widget.addTab(self._create_encrypt_tab(), "加密/解密")
        self.tab_widget.addTab(self._create_metadata_tab(), "元数据编辑")
        self.tab_widget.addTab(self._create_convert_tab(), "PDF转图片")
        
        layout.addWidget(self.tab_widget, 1)
        
        return panel
    
    def _create_merge_tab(self) -> QWidget:
        """
        创建合并PDF标签页
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        info_label = QLabel("将列表中的多个PDF文件合并为一个PDF文件。\n文件将按照列表中的顺序合并。")
        info_label.setStyleSheet("color: #666; padding: 5px; background-color: #e3f2fd; border-radius: 4px;")
        layout.addWidget(info_label)
        
        order_group = QGroupBox("合并顺序调整")
        order_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        order_layout = QHBoxLayout(order_group)
        order_layout.setContentsMargins(10, 15, 10, 10)
        order_layout.setSpacing(10)
        
        up_btn = QPushButton("上移")
        up_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        up_btn.clicked.connect(self._on_move_up)
        order_layout.addWidget(up_btn)
        
        down_btn = QPushButton("下移")
        down_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        down_btn.clicked.connect(self._on_move_down)
        order_layout.addWidget(down_btn)
        
        order_layout.addStretch()
        
        layout.addWidget(order_group)
        
        output_group = QGroupBox("输出设置")
        output_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        output_layout = QFormLayout(output_group)
        output_layout.setContentsMargins(10, 15, 10, 10)
        output_layout.setSpacing(10)
        
        self.merge_output_name = QLineEdit()
        self.merge_output_name.setPlaceholderText("merged.pdf")
        self.merge_output_name.setText("merged.pdf")
        self.merge_output_name.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        output_layout.addRow("输出文件名:", self.merge_output_name)
        
        layout.addWidget(output_group)
        
        merge_btn = QPushButton("开始合并")
        merge_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        merge_btn.clicked.connect(self._on_merge_pdf)
        layout.addWidget(merge_btn)
        
        layout.addStretch()
        
        return widget
    
    def _create_split_tab(self) -> QWidget:
        """
        创建拆分PDF标签页
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        info_label = QLabel("将选中的PDF文件拆分为多个PDF文件。\n支持按页数拆分或按范围拆分。")
        info_label.setStyleSheet("color: #666; padding: 5px; background-color: #e3f2fd; border-radius: 4px;")
        layout.addWidget(info_label)
        
        split_group = QGroupBox("拆分方式")
        split_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        split_layout = QFormLayout(split_group)
        split_layout.setContentsMargins(10, 15, 10, 10)
        split_layout.setSpacing(10)
        
        self.split_mode = QComboBox()
        self.split_mode.addItems(["每N页拆分", "按页码范围拆分", "每页一个文件"])
        self.split_mode.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        self.split_mode.currentIndexChanged.connect(self._on_split_mode_changed)
        split_layout.addRow("拆分方式:", self.split_mode)
        
        self.split_pages_label = QLabel("每页数量:")
        split_layout.addRow(self.split_pages_label)
        
        self.split_pages_spin = QSpinBox()
        self.split_pages_spin.setRange(1, 1000)
        self.split_pages_spin.setValue(1)
        self.split_pages_spin.setStyleSheet("""
            QSpinBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        split_layout.addRow(self.split_pages_spin)
        
        self.split_range_label = QLabel("页码范围:")
        self.split_range_label.hide()
        split_layout.addRow(self.split_range_label)
        
        self.split_range_edit = QLineEdit()
        self.split_range_edit.setPlaceholderText("例如: 1-5, 8, 10-15")
        self.split_range_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        self.split_range_edit.hide()
        split_layout.addRow(self.split_range_edit)
        
        layout.addWidget(split_group)
        
        output_group = QGroupBox("输出设置")
        output_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        output_layout = QFormLayout(output_group)
        output_layout.setContentsMargins(10, 15, 10, 10)
        output_layout.setSpacing(10)
        
        self.split_output_prefix = QLineEdit()
        self.split_output_prefix.setPlaceholderText("split_")
        self.split_output_prefix.setText("split_")
        self.split_output_prefix.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        output_layout.addRow("输出文件名前缀:", self.split_output_prefix)
        
        layout.addWidget(output_group)
        
        split_btn = QPushButton("开始拆分")
        split_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        split_btn.clicked.connect(self._on_split_pdf)
        layout.addWidget(split_btn)
        
        layout.addStretch()
        
        return widget
    
    def _create_rotate_tab(self) -> QWidget:
        """
        创建旋转页面标签页
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        info_label = QLabel("旋转PDF文件中的页面。\n支持旋转选中页面或所有页面。")
        info_label.setStyleSheet("color: #666; padding: 5px; background-color: #e3f2fd; border-radius: 4px;")
        layout.addWidget(info_label)
        
        rotate_group = QGroupBox("旋转设置")
        rotate_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        rotate_layout = QFormLayout(rotate_group)
        rotate_layout.setContentsMargins(10, 15, 10, 10)
        rotate_layout.setSpacing(10)
        
        self.rotate_angle = QComboBox()
        self.rotate_angle.addItems(["顺时针90°", "顺时针180°", "逆时针90°"])
        self.rotate_angle.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        rotate_layout.addRow("旋转角度:", self.rotate_angle)
        
        self.rotate_all = QCheckBox("旋转所有页面")
        self.rotate_all.setChecked(True)
        self.rotate_all.stateChanged.connect(self._on_rotate_all_changed)
        rotate_layout.addRow(self.rotate_all)
        
        self.rotate_pages_label = QLabel("页码范围:")
        self.rotate_pages_label.hide()
        rotate_layout.addRow(self.rotate_pages_label)
        
        self.rotate_pages_edit = QLineEdit()
        self.rotate_pages_edit.setPlaceholderText("例如: 1, 3-5")
        self.rotate_pages_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        self.rotate_pages_edit.hide()
        rotate_layout.addRow(self.rotate_pages_edit)
        
        layout.addWidget(rotate_group)
        
        output_group = QGroupBox("输出设置")
        output_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        output_layout = QFormLayout(output_group)
        output_layout.setContentsMargins(10, 15, 10, 10)
        output_layout.setSpacing(10)
        
        self.rotate_output_name = QLineEdit()
        self.rotate_output_name.setPlaceholderText("rotated.pdf")
        self.rotate_output_name.setText("rotated.pdf")
        self.rotate_output_name.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        output_layout.addRow("输出文件名:", self.rotate_output_name)
        
        layout.addWidget(output_group)
        
        rotate_btn = QPushButton("开始旋转")
        rotate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        rotate_btn.clicked.connect(self._on_rotate_pdf)
        layout.addWidget(rotate_btn)
        
        layout.addStretch()
        
        return widget
    
    def _create_encrypt_tab(self) -> QWidget:
        """
        创建加密/解密标签页
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        info_label = QLabel("为PDF文件添加密码保护或移除密码保护。")
        info_label.setStyleSheet("color: #666; padding: 5px; background-color: #e3f2fd; border-radius: 4px;")
        layout.addWidget(info_label)
        
        encrypt_group = QGroupBox("加密设置")
        encrypt_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        encrypt_layout = QFormLayout(encrypt_group)
        encrypt_layout.setContentsMargins(10, 15, 10, 10)
        encrypt_layout.setSpacing(10)
        
        self.encrypt_user_pass = QLineEdit()
        self.encrypt_user_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.encrypt_user_pass.setPlaceholderText("用户密码（打开文件时需要")
        self.encrypt_user_pass.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        encrypt_layout.addRow("用户密码:", self.encrypt_user_pass)
        
        self.encrypt_owner_pass = QLineEdit()
        self.encrypt_owner_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.encrypt_owner_pass.setPlaceholderText("所有者密码（完全权限）")
        self.encrypt_owner_pass.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        encrypt_layout.addRow("所有者密码:", self.encrypt_owner_pass)
        
        layout.addWidget(encrypt_group)
        
        output_group = QGroupBox("输出设置")
        output_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        output_layout = QFormLayout(output_group)
        output_layout.setContentsMargins(10, 15, 10, 10)
        output_layout.setSpacing(10)
        
        self.encrypt_output_name = QLineEdit()
        self.encrypt_output_name.setPlaceholderText("encrypted.pdf")
        self.encrypt_output_name.setText("encrypted.pdf")
        self.encrypt_output_name.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        output_layout.addRow("输出文件名:", self.encrypt_output_name)
        
        layout.addWidget(output_group)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        encrypt_btn = QPushButton("加密PDF")
        encrypt_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        encrypt_btn.clicked.connect(self._on_encrypt_pdf)
        btn_layout.addWidget(encrypt_btn)
        
        decrypt_btn = QPushButton("解密PDF")
        decrypt_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        decrypt_btn.clicked.connect(self._on_decrypt_pdf)
        btn_layout.addWidget(decrypt_btn)
        
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
        return widget
    
    def _create_metadata_tab(self) -> QWidget:
        """
        创建元数据编辑标签页
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        info_label = QLabel("查看和编辑PDF文件的元数据信息。")
        info_label.setStyleSheet("color: #666; padding: 5px; background-color: #e3f2fd; border-radius: 4px;")
        layout.addWidget(info_label)
        
        meta_group = QGroupBox("元数据信息")
        meta_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        meta_layout = QFormLayout(meta_group)
        meta_layout.setContentsMargins(10, 15, 10, 10)
        meta_layout.setSpacing(10)
        
        self.meta_title = QLineEdit()
        self.meta_title.setPlaceholderText("文档标题")
        self.meta_title.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        meta_layout.addRow("标题:", self.meta_title)
        
        self.meta_author = QLineEdit()
        self.meta_author.setPlaceholderText("作者")
        self.meta_author.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        meta_layout.addRow("作者:", self.meta_author)
        
        self.meta_subject = QLineEdit()
        self.meta_subject.setPlaceholderText("主题")
        self.meta_subject.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        meta_layout.addRow("主题:", self.meta_subject)
        
        self.meta_keywords = QLineEdit()
        self.meta_keywords.setPlaceholderText("关键字（用逗号分隔）")
        self.meta_keywords.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        meta_layout.addRow("关键字:", self.meta_keywords)
        
        self.meta_creator = QLineEdit()
        self.meta_creator.setPlaceholderText("创建者")
        self.meta_creator.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        meta_layout.addRow("创建者:", self.meta_creator)
        
        layout.addWidget(meta_group)
        
        output_group = QGroupBox("输出设置")
        output_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        output_layout = QFormLayout(output_group)
        output_layout.setContentsMargins(10, 15, 10, 10)
        output_layout.setSpacing(10)
        
        self.meta_output_name = QLineEdit()
        self.meta_output_name.setPlaceholderText("metadata_updated.pdf")
        self.meta_output_name.setText("metadata_updated.pdf")
        self.meta_output_name.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        output_layout.addRow("输出文件名:", self.meta_output_name)
        
        layout.addWidget(output_group)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        load_btn = QPushButton("加载元数据")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        load_btn.clicked.connect(self._on_load_metadata)
        btn_layout.addWidget(load_btn)
        
        save_btn = QPushButton("保存元数据")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self._on_save_metadata)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
        return widget
    
    def _create_convert_tab(self) -> QWidget:
        """
        创建PDF转图片标签页
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        info_label = QLabel("将PDF文件转换为图片格式。\n支持JPG、PNG等格式。")
        info_label.setStyleSheet("color: #666; padding: 5px; background-color: #e3f2fd; border-radius: 4px;")
        layout.addWidget(info_label)
        
        convert_group = QGroupBox("转换设置")
        convert_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        convert_layout = QFormLayout(convert_group)
        convert_layout.setContentsMargins(10, 15, 10, 10)
        convert_layout.setSpacing(10)
        
        self.convert_format = QComboBox()
        self.convert_format.addItems(["PNG", "JPEG", "BMP", "TIFF"])
        self.convert_format.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        convert_layout.addRow("输出格式:", self.convert_format)
        
        self.convert_dpi = QSpinBox()
        self.convert_dpi.setRange(72, 600)
        self.convert_dpi.setValue(150)
        self.convert_dpi.setStyleSheet("""
            QSpinBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        convert_layout.addRow("DPI (分辨率):", self.convert_dpi)
        
        self.convert_range_check = QCheckBox("只转换指定页面")
        self.convert_range_check.setChecked(False)
        self.convert_range_check.stateChanged.connect(self._on_convert_range_changed)
        convert_layout.addRow(self.convert_range_check)
        
        self.convert_range_label = QLabel("页码范围:")
        self.convert_range_label.hide()
        convert_layout.addRow(self.convert_range_label)
        
        self.convert_range_edit = QLineEdit()
        self.convert_range_edit.setPlaceholderText("例如: 1, 3-5")
        self.convert_range_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        self.convert_range_edit.hide()
        convert_layout.addRow(self.convert_range_edit)
        
        layout.addWidget(convert_group)
        
        output_group = QGroupBox("输出设置")
        output_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        output_layout = QFormLayout(output_group)
        output_layout.setContentsMargins(10, 15, 10, 10)
        output_layout.setSpacing(10)
        
        self.convert_output_prefix = QLineEdit()
        self.convert_output_prefix.setPlaceholderText("page_")
        self.convert_output_prefix.setText("page_")
        self.convert_output_prefix.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        output_layout.addRow("输出文件名前缀:", self.convert_output_prefix)
        
        layout.addWidget(output_group)
        
        convert_btn = QPushButton("开始转换")
        convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        convert_btn.clicked.connect(self._on_convert_to_image)
        layout.addWidget(convert_btn)
        
        layout.addStretch()
        
        return widget
    
    def _on_add_pdf(self):
        """
        添加PDF文件
        """
        file_paths, _ = QFileDialog.getOpenFileNames(
            None, "选择PDF文件", "",
            "PDF文件 (*.pdf);;所有文件 (*)"
        )
        
        if file_paths:
            for file_path in file_paths:
                if file_path.lower().endswith('.pdf'):
                    file_info = {
                        'path': file_path,
                        'name': os.path.basename(file_path),
                        'size': os.path.getsize(file_path)
                    }
                    self._current_pdf_files.append(file_info)
            
            self._refresh_pdf_list()
    
    def _on_remove_pdf(self):
        """
        移除选中的PDF文件
        """
        current_row = self.pdf_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(None, "警告", "请先选择要移除的文件！")
            return
        
        del self._current_pdf_files[current_row]
        self._refresh_pdf_list()
        self._clear_file_info()
    
    def _on_clear_list(self):
        """
        清空PDF文件列表
        """
        if self._current_pdf_files:
            reply = QMessageBox.question(
                None, "确认清空",
                "确定要清空所有PDF文件吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._current_pdf_files = []
                self._refresh_pdf_list()
                self._clear_file_info()
    
    def _refresh_pdf_list(self):
        """
        刷新PDF文件列表
        """
        self.pdf_list.clear()
        
        for i, pdf_file in enumerate(self._current_pdf_files):
            size_mb = pdf_file['size'] / (1024 * 1024)
            display_text = f"{i + 1}. {pdf_file['name']}\n   ({size_mb:.2f} MB)"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.pdf_list.addItem(item)
    
    def _on_pdf_selected(self, index):
        """
        当选择PDF文件时触发
        """
        if index < 0 or index >= len(self._current_pdf_files):
            self._clear_file_info()
            return
        
        pdf_file = self._current_pdf_files[index]
        self._current_selected_pdf = pdf_file
        
        info_text = f"文件名: {pdf_file['name']}\n"
        info_text += f"路径: {pdf_file['path']}\n"
        info_text += f"大小: {pdf_file['size'] / (1024 * 1024):.2f} MB\n"
        
        if PYPDF_AVAILABLE:
            try:
                reader = PdfReader(pdf_file['path'])
                info_text += f"页数: {len(reader.pages)} 页\n"
                info_text += f"加密: {'是' if reader.is_encrypted else '否'}\n"
                
                if reader.metadata:
                    if reader.metadata.title:
                        info_text += f"标题: {reader.metadata.title}\n"
                    if reader.metadata.author:
                        info_text += f"作者: {reader.metadata.author}\n"
            except Exception as e:
                info_text += f"\n读取信息失败: {e}"
        
        self.file_info_label.setText(info_text)
    
    def _clear_file_info(self):
        """
        清空文件信息
        """
        self._current_selected_pdf = None
        self.file_info_label.setText("未选择文件")
        
        self.meta_title.clear()
        self.meta_author.clear()
        self.meta_subject.clear()
        self.meta_keywords.clear()
        self.meta_creator.clear()
    
    def _on_move_up(self):
        """
        上移选中的文件
        """
        current_row = self.pdf_list.currentRow()
        if current_row <= 0:
            return
        
        self._current_pdf_files[current_row], self._current_pdf_files[current_row - 1] = \
            self._current_pdf_files[current_row - 1], self._current_pdf_files[current_row]
        
        self._refresh_pdf_list()
        self.pdf_list.setCurrentRow(current_row - 1)
    
    def _on_move_down(self):
        """
        下移选中的文件
        """
        current_row = self.pdf_list.currentRow()
        if current_row < 0 or current_row >= len(self._current_pdf_files) - 1:
            return
        
        self._current_pdf_files[current_row], self._current_pdf_files[current_row + 1] = \
            self._current_pdf_files[current_row + 1], self._current_pdf_files[current_row]
        
        self._refresh_pdf_list()
        self.pdf_list.setCurrentRow(current_row + 1)
    
    def _on_split_mode_changed(self, index):
        """
        拆分模式改变
        """
        if index == 2:
            self.split_pages_label.hide()
            self.split_pages_spin.hide()
            self.split_range_label.hide()
            self.split_range_edit.hide()
        elif index == 1:
            self.split_pages_label.hide()
            self.split_pages_spin.hide()
            self.split_range_label.show()
            self.split_range_edit.show()
        else:
            self.split_pages_label.show()
            self.split_pages_spin.show()
            self.split_range_label.hide()
            self.split_range_edit.hide()
    
    def _on_rotate_all_changed(self, state):
        """
        旋转所有页面选项改变
        """
        is_checked = state == Qt.CheckState.Checked.value
        self.rotate_pages_label.setHidden(is_checked)
        self.rotate_pages_edit.setHidden(is_checked)
    
    def _on_convert_range_changed(self, state):
        """
        转换范围选项改变
        """
        is_checked = state == Qt.CheckState.Checked.value
        self.convert_range_label.setHidden(not is_checked)
        self.convert_range_edit.setHidden(not is_checked)
    
    def _save_operation(self, operation: str, source: str, target: str, details: str = ""):
        """
        保存操作到历史记录
        """
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        self._db.insert('pdf_operations', {
            'operation': operation,
            'source_file': source,
            'target_file': target,
            'details': details,
            'created_at': now
        })
    
    def _on_merge_pdf(self):
        """
        合并PDF文件
        """
        if not PYPDF_AVAILABLE:
            QMessageBox.critical(None, "错误", "pypdf库未安装！请运行: pip install pypdf")
            return
        
        if len(self._current_pdf_files) < 2:
            QMessageBox.warning(None, "警告", "请至少添加2个PDF文件才能合并！")
            return
        
        output_name = self.merge_output_name.text().strip()
        if not output_name:
            output_name = "merged.pdf"
        if not output_name.lower().endswith('.pdf'):
            output_name += '.pdf'
        
        output_path, _ = QFileDialog.getSaveFileName(
            None, "保存合并后的PDF", output_name,
            "PDF文件 (*.pdf)"
        )
        
        if not output_path:
            return
        
        try:
            writer = PdfWriter()
            
            for pdf_file in self._current_pdf_files:
                reader = PdfReader(pdf_file['path'])
                
                if reader.is_encrypted:
                    QMessageBox.warning(None, "警告", f"文件 {pdf_file['name']} 已加密，无法合并！")
                    return
                
                for page in reader.pages:
                    writer.add_page(page)
            
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            
            self._save_operation(
                "合并PDF",
                ", ".join([f['name'] for f in self._current_pdf_files]),
                output_path,
                f"合并了 {len(self._current_pdf_files)} 个文件"
            )
            
            QMessageBox.information(None, "成功", f"PDF合并成功！\n保存路径: {output_path}")
            
        except Exception as e:
            QMessageBox.critical(None, "错误", f"合并PDF失败: {e}")
    
    def _on_split_pdf(self):
        """
        拆分PDF文件
        """
        if not PYPDF_AVAILABLE:
            QMessageBox.critical(None, "错误", "pypdf库未安装！请运行: pip install pypdf")
            return
        
        if not self._current_selected_pdf:
            QMessageBox.warning(None, "警告", "请先选择要拆分的PDF文件！")
            return
        
        output_dir = QFileDialog.getExistingDirectory(None, "选择输出目录")
        if not output_dir:
            return
        
        prefix = self.split_output_prefix.text().strip()
        if not prefix:
            prefix = "split_"
        
        try:
            reader = PdfReader(self._current_selected_pdf['path'])
            
            if reader.is_encrypted:
                QMessageBox.warning(None, "警告", "该PDF文件已加密，无法拆分！")
                return
            
            total_pages = len(reader.pages)
            split_mode = self.split_mode.currentIndex()
            split_count = 0
            
            if split_mode == 2:
                for i in range(total_pages):
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])
                    
                    output_path = os.path.join(output_dir, f"{prefix}{i + 1}.pdf")
                    with open(output_path, "wb") as output_file:
                        writer.write(output_file)
                    split_count += 1
            
            elif split_mode == 1:
                range_text = self.split_range_edit.text().strip()
                if not range_text:
                    QMessageBox.warning(None, "警告", "请输入页码范围！")
                    return
                
                pages_to_extract = self._parse_page_range(range_text, total_pages)
                if not pages_to_extract:
                    QMessageBox.warning(None, "警告", "无效的页码范围！")
                    return
                
                for page_num in pages_to_extract:
                    writer = PdfWriter()
                    writer.add_page(reader.pages[page_num - 1])
                    
                    output_path = os.path.join(output_dir, f"{prefix}page_{page_num}.pdf")
                    with open(output_path, "wb") as output_file:
                        writer.write(output_file)
                    split_count += 1
            
            else:
                pages_per_file = self.split_pages_spin.value()
                file_index = 1
                
                for i in range(0, total_pages, pages_per_file):
                    writer = PdfWriter()
                    
                    end_page = min(i + pages_per_file, total_pages)
                    for j in range(i, end_page):
                        writer.add_page(reader.pages[j])
                    
                    output_path = os.path.join(output_dir, f"{prefix}{file_index}.pdf")
                    with open(output_path, "wb") as output_file:
                        writer.write(output_file)
                    
                    file_index += 1
                    split_count += 1
            
            self._save_operation(
                "拆分PDF",
                self._current_selected_pdf['name'],
                output_dir,
                f"拆分为 {split_count} 个文件"
            )
            
            QMessageBox.information(None, "成功", f"PDF拆分成功！\n共生成 {split_count} 个文件\n保存目录: {output_dir}")
            
        except Exception as e:
            QMessageBox.critical(None, "错误", f"拆分PDF失败: {e}")
    
    def _parse_page_range(self, range_text: str, total_pages: int) -> List[int]:
        """
        解析页码范围
        """
        pages = []
        parts = range_text.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    for p in range(start, end + 1):
                        if 1 <= p <= total_pages:
                            pages.append(p)
                except:
                    pass
            else:
                try:
                    p = int(part)
                    if 1 <= p <= total_pages:
                        pages.append(p)
                except:
                    pass
        
        return sorted(list(set(pages)))
    
    def _on_rotate_pdf(self):
        """
        旋转PDF页面
        """
        if not PYPDF_AVAILABLE:
            QMessageBox.critical(None, "错误", "pypdf库未安装！请运行: pip install pypdf")
            return
        
        if not self._current_selected_pdf:
            QMessageBox.warning(None, "警告", "请先选择要旋转的PDF文件！")
            return
        
        output_name = self.rotate_output_name.text().strip()
        if not output_name:
            output_name = "rotated.pdf"
        if not output_name.lower().endswith('.pdf'):
            output_name += '.pdf'
        
        output_path, _ = QFileDialog.getSaveFileName(
            None, "保存旋转后的PDF", output_name,
            "PDF文件 (*.pdf)"
        )
        
        if not output_path:
            return
        
        try:
            reader = PdfReader(self._current_selected_pdf['path'])
            
            if reader.is_encrypted:
                QMessageBox.warning(None, "警告", "该PDF文件已加密，无法旋转！")
                return
            
            angle_map = {0: 90, 1: 180, 2: 270}
            rotation_angle = angle_map[self.rotate_angle.currentIndex()]
            
            writer = PdfWriter()
            
            if self.rotate_all.isChecked():
                for page in reader.pages:
                    page.rotate(rotation_angle)
                    writer.add_page(page)
            else:
                range_text = self.rotate_pages_edit.text().strip()
                if not range_text:
                    QMessageBox.warning(None, "警告", "请输入页码范围！")
                    return
                
                pages_to_rotate = self._parse_page_range(range_text, len(reader.pages))
                if not pages_to_rotate:
                    QMessageBox.warning(None, "警告", "无效的页码范围！")
                    return
                
                for i, page in enumerate(reader.pages):
                    if (i + 1) in pages_to_rotate:
                        page.rotate(rotation_angle)
                    writer.add_page(page)
            
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            
            self._save_operation(
                "旋转PDF",
                self._current_selected_pdf['name'],
                output_path,
                f"旋转角度: {rotation_angle}°"
            )
            
            QMessageBox.information(None, "成功", f"PDF旋转成功！\n保存路径: {output_path}")
            
        except Exception as e:
            QMessageBox.critical(None, "错误", f"旋转PDF失败: {e}")
    
    def _on_encrypt_pdf(self):
        """
        加密PDF文件
        """
        if not PYPDF_AVAILABLE:
            QMessageBox.critical(None, "错误", "pypdf库未安装！请运行: pip install pypdf")
            return
        
        if not self._current_selected_pdf:
            QMessageBox.warning(None, "警告", "请先选择要加密的PDF文件！")
            return
        
        user_pass = self.encrypt_user_pass.text()
        owner_pass = self.encrypt_owner_pass.text()
        
        if not user_pass and not owner_pass:
            QMessageBox.warning(None, "警告", "请至少输入一个密码！")
            return
        
        output_name = self.encrypt_output_name.text().strip()
        if not output_name:
            output_name = "encrypted.pdf"
        if not output_name.lower().endswith('.pdf'):
            output_name += '.pdf'
        
        output_path, _ = QFileDialog.getSaveFileName(
            None, "保存加密后的PDF", output_name,
            "PDF文件 (*.pdf)"
        )
        
        if not output_path:
            return
        
        try:
            reader = PdfReader(self._current_selected_pdf['path'])
            
            if reader.is_encrypted:
                QMessageBox.warning(None, "警告", "该PDF文件已加密！")
                return
            
            writer = PdfWriter()
            
            for page in reader.pages:
                writer.add_page(page)
            
            if user_pass or owner_pass:
                writer.encrypt(
                    user_password=user_pass if user_pass else "",
                    owner_password=owner_pass if owner_pass else user_pass,
                    use_128bit=True
                )
            
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            
            self._save_operation(
                "加密PDF",
                self._current_selected_pdf['name'],
                output_path,
                "PDF已加密"
            )
            
            QMessageBox.information(None, "成功", f"PDF加密成功！\n保存路径: {output_path}")
            
        except Exception as e:
            QMessageBox.critical(None, "错误", f"加密PDF失败: {e}")
    
    def _on_decrypt_pdf(self):
        """
        解密PDF文件
        """
        if not PYPDF_AVAILABLE:
            QMessageBox.critical(None, "错误", "pypdf库未安装！请运行: pip install pypdf")
            return
        
        if not self._current_selected_pdf:
            QMessageBox.warning(None, "警告", "请先选择要解密的PDF文件！")
            return
        
        try:
            reader = PdfReader(self._current_selected_pdf['path'])
            
            if not reader.is_encrypted:
                QMessageBox.warning(None, "警告", "该PDF文件未加密！")
                return
            
            password, ok = QInputDialog.getText(
                None, "输入密码", "请输入PDF密码:",
                QLineEdit.EchoMode.Password
            )
            
            if not ok or not password:
                return
            
            reader = PdfReader(self._current_selected_pdf['path'], password=password)
            
            output_name = "decrypted.pdf"
            output_path, _ = QFileDialog.getSaveFileName(
                None, "保存解密后的PDF", output_name,
                "PDF文件 (*.pdf)"
            )
            
            if not output_path:
                return
            
            writer = PdfWriter()
            
            for page in reader.pages:
                writer.add_page(page)
            
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            
            self._save_operation(
                "解密PDF",
                self._current_selected_pdf['name'],
                output_path,
                "PDF已解密"
            )
            
            QMessageBox.information(None, "成功", f"PDF解密成功！\n保存路径: {output_path}")
            
        except Exception as e:
            QMessageBox.critical(None, "错误", f"解密PDF失败: {e}\n请确认密码是否正确。")
    
    def _on_load_metadata(self):
        """
        加载PDF元数据
        """
        if not PYPDF_AVAILABLE:
            QMessageBox.critical(None, "错误", "pypdf库未安装！请运行: pip install pypdf")
            return
        
        if not self._current_selected_pdf:
            QMessageBox.warning(None, "警告", "请先选择PDF文件！")
            return
        
        try:
            reader = PdfReader(self._current_selected_pdf['path'])
            
            if reader.is_encrypted:
                QMessageBox.warning(None, "警告", "该PDF文件已加密，无法读取元数据！")
                return
            
            if reader.metadata:
                if reader.metadata.title:
                    self.meta_title.setText(str(reader.metadata.title))
                else:
                    self.meta_title.clear()
                
                if reader.metadata.author:
                    self.meta_author.setText(str(reader.metadata.author))
                else:
                    self.meta_author.clear()
                
                if reader.metadata.subject:
                    self.meta_subject.setText(str(reader.metadata.subject))
                else:
                    self.meta_subject.clear()
                
                if reader.metadata.keywords:
                    self.meta_keywords.setText(str(reader.metadata.keywords))
                else:
                    self.meta_keywords.clear()
                
                if reader.metadata.creator:
                    self.meta_creator.setText(str(reader.metadata.creator))
                else:
                    self.meta_creator.clear()
            
            QMessageBox.information(None, "成功", "元数据加载成功！")
            
        except Exception as e:
            QMessageBox.critical(None, "错误", f"加载元数据失败: {e}")
    
    def _on_save_metadata(self):
        """
        保存PDF元数据
        """
        if not PYPDF_AVAILABLE:
            QMessageBox.critical(None, "错误", "pypdf库未安装！请运行: pip install pypdf")
            return
        
        if not self._current_selected_pdf:
            QMessageBox.warning(None, "警告", "请先选择PDF文件！")
            return
        
        output_name = self.meta_output_name.text().strip()
        if not output_name:
            output_name = "metadata_updated.pdf"
        if not output_name.lower().endswith('.pdf'):
            output_name += '.pdf'
        
        output_path, _ = QFileDialog.getSaveFileName(
            None, "保存更新后的PDF", output_name,
            "PDF文件 (*.pdf)"
        )
        
        if not output_path:
            return
        
        try:
            reader = PdfReader(self._current_selected_pdf['path'])
            
            if reader.is_encrypted:
                QMessageBox.warning(None, "警告", "该PDF文件已加密，无法编辑元数据！")
                return
            
            writer = PdfWriter()
            
            for page in reader.pages:
                writer.add_page(page)
            
            metadata = {
                '/Title': self.meta_title.text() or "",
                '/Author': self.meta_author.text() or "",
                '/Subject': self.meta_subject.text() or "",
                '/Keywords': self.meta_keywords.text() or "",
                '/Creator': self.meta_creator.text() or ""
            }
            
            writer.add_metadata(metadata)
            
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            
            self._save_operation(
                "编辑元数据",
                self._current_selected_pdf['name'],
                output_path,
                "PDF元数据已更新"
            )
            
            QMessageBox.information(None, "成功", f"元数据保存成功！\n保存路径: {output_path}")
            
        except Exception as e:
            QMessageBox.critical(None, "错误", f"保存元数据失败: {e}")
    
    def _on_convert_to_image(self):
        """
        将PDF转换为图片
        """
        if not PDF2IMAGE_AVAILABLE:
            QMessageBox.critical(
                None, "错误",
                "pdf2image库未安装！\n"
                "请运行: pip install pdf2image\n\n"
                "注意: 还需要安装poppler工具。\n"
                "Windows用户请从 https://github.com/oschwartz10612/poppler-windows/releases 下载poppler，\n"
                "并将bin目录添加到系统PATH环境变量中。"
            )
            return
        
        if not self._current_selected_pdf:
            QMessageBox.warning(None, "警告", "请先选择要转换的PDF文件！")
            return
        
        output_dir = QFileDialog.getExistingDirectory(None, "选择输出目录")
        if not output_dir:
            return
        
        prefix = self.convert_output_prefix.text().strip()
        if not prefix:
            prefix = "page_"
        
        try:
            format_map = {"PNG": "png", "JPEG": "jpg", "BMP": "bmp", "TIFF": "tiff"}
            output_format = format_map[self.convert_format.currentText()]
            dpi = self.convert_dpi.value()
            
            pages_to_convert = None
            if self.convert_range_check.isChecked():
                range_text = self.convert_range_edit.text().strip()
                if range_text:
                    try:
                        reader = PdfReader(self._current_selected_pdf['path'])
                        total_pages = len(reader.pages)
                        pages_to_convert = self._parse_page_range(range_text, total_pages)
                    except:
                        pass
            
            images = convert_from_path(
                self._current_selected_pdf['path'],
                dpi=dpi,
                fmt=output_format,
                output_folder=output_dir,
                output_file=prefix
            )
            
            if pages_to_convert:
                temp_dir = tempfile.mkdtemp()
                all_images = convert_from_path(
                    self._current_selected_pdf['path'],
                    dpi=dpi,
                    fmt=output_format
                )
                
                for page_num in pages_to_convert:
                    if 1 <= page_num <= len(all_images):
                        image = all_images[page_num - 1]
                        output_path = os.path.join(output_dir, f"{prefix}{page_num}.{output_format}")
                        image.save(output_path, output_format.upper())
                
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                converted_count = len(pages_to_convert)
            else:
                converted_count = len(images)
            
            self._save_operation(
                "PDF转图片",
                self._current_selected_pdf['name'],
                output_dir,
                f"转换了 {converted_count} 页，格式: {output_format.upper()}, DPI: {dpi}"
            )
            
            QMessageBox.information(
                None, "成功",
                f"PDF转图片成功！\n"
                f"共转换 {converted_count} 页\n"
                f"保存目录: {output_dir}\n"
                f"格式: {output_format.upper()}\n"
                f"DPI: {dpi}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                None, "错误",
                f"转换失败: {e}\n\n"
                "请确保已安装poppler工具并配置好PATH环境变量。"
            )
    
    def _on_show_history(self):
        """
        显示操作历史记录
        """
        histories = self._db.query_all("""
            SELECT id, operation, source_file, target_file, details, created_at 
            FROM pdf_operations 
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        if not histories:
            QMessageBox.information(None, "提示", "暂无操作历史记录")
            return
        
        history_text = "PDF操作历史记录（最近50条）:\n\n"
        for h in histories:
            history_text += f"[{h['created_at']}\n"
            history_text += f"操作: {h['operation']}\n"
            if h['source_file']:
                history_text += f"源文件: {h['source_file']}\n"
            if h['target_file']:
                history_text += f"目标: {h['target_file']}\n"
            if h['details']:
                history_text += f"详情: {h['details']}\n"
            history_text += "-" * 40 + "\n"
        
        msg = QMessageBox()
        msg.setWindowTitle("操作历史")
        msg.setText(history_text)
        msg.setStyleSheet("QLabel{min-width: 600px;}")
        msg.exec()