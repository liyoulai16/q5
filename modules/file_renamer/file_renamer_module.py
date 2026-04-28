#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件批量重命名模块
生活工具分类下的文件批量重命名功能
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QGroupBox, QGridLayout,
                             QScrollArea, QFrame, QMessageBox, QTabWidget, QCheckBox,
                             QSplitter, QSpinBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFileDialog, QRadioButton, QButtonGroup,
                             QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont, QColor, QBrush, QFontMetrics, QPalette

from modules.module_manager import BaseModule, ModuleCategory


class RenameRuleType(Enum):
    ADD_PREFIX = "add_prefix"
    ADD_SUFFIX = "add_suffix"
    REPLACE = "replace"
    DELETE = "delete"
    INSERT = "insert"
    SEQUENCE = "sequence"
    CASE_CHANGE = "case_change"
    EXTENSION_CHANGE = "extension_change"


class CaseChangeType(Enum):
    UPPER = "upper"
    LOWER = "lower"
    CAPITALIZE = "capitalize"
    TITLE = "title"


@dataclass
class RenameRule:
    rule_type: RenameRuleType
    parameters: Dict[str, Any]


@dataclass
class FileItem:
    original_name: str
    original_path: str
    is_directory: bool
    new_name: str = ""
    size: int = 0
    modified_time: datetime = None


@dataclass
class RenameHistory:
    original_path: str
    new_path: str
    original_name: str
    new_name: str


class FileRenamerWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(bool, int, list)
    error = pyqtSignal(str)

    def __init__(self, rename_operations: List[RenameHistory], parent=None):
        super().__init__(parent)
        self.rename_operations = rename_operations
        self.history = []

    def run(self):
        success_count = 0
        errors = []
        total = len(self.rename_operations)

        for i, op in enumerate(self.rename_operations):
            self.progress.emit(i + 1, total)
            try:
                if os.path.exists(op.new_path):
                    raise FileExistsError(f"目标文件已存在: {op.new_name}")
                os.rename(op.original_path, op.new_path)
                self.history.append(op)
                success_count += 1
            except Exception as e:
                errors.append(f"{op.original_name}: {str(e)}")

        self.finished.emit(len(errors) == 0, success_count, errors)


class FileRenamerModule(BaseModule):
    """
    文件批量重命名模块
    提供多种重命名规则，支持预览、执行和撤销功能
    """

    @property
    def module_id(self) -> str:
        return "file_renamer"

    @property
    def name(self) -> str:
        return "文件批量重命名"

    @property
    def description(self) -> str:
        return "强大的文件批量重命名工具，支持多种重命名规则，包含前缀、后缀、替换、删除、插入、序列编号、大小写转换和扩展名修改"

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
        self._files: List[FileItem] = []
        self._rename_history: List[List[RenameHistory]] = []
        self._current_rules: List[RenameRule] = []

    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        pass

    def _create_widget(self) -> QWidget:
        """
        创建文件批量重命名的主界面
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        header_layout = self._create_header()
        main_layout.addLayout(header_layout)

        content_splitter = QSplitter(Qt.Orientation.Vertical)
        content_splitter.setChildrenCollapsible(False)

        rules_panel = self._create_rules_panel()
        content_splitter.addWidget(rules_panel)

        files_panel = self._create_files_panel()
        content_splitter.addWidget(files_panel)

        content_splitter.setSizes([400, 350])
        main_layout.addWidget(content_splitter, 1)

        action_bar = self._create_action_bar()
        main_layout.addLayout(action_bar)

        return widget

    def _create_header(self) -> QHBoxLayout:
        """
        创建头部区域
        """
        layout = QHBoxLayout()
        layout.setSpacing(15)

        title_label = QLabel("📁 文件批量重命名")
        title_label.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        layout.addWidget(title_label)

        layout.addStretch()

        self._file_count_label = QLabel("已选择: 0 个文件/文件夹")
        self._file_count_label.setFont(QFont("Microsoft YaHei", 11))
        self._file_count_label.setStyleSheet("color: #666666;")
        layout.addWidget(self._file_count_label)

        return layout

    def _create_rules_panel(self) -> QWidget:
        """
        创建重命名规则面板
        """
        panel = QGroupBox("重命名规则")
        panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #1565C0;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(15)

        self._tab_widget = QTabWidget()
        self._tab_widget.setFont(QFont("Microsoft YaHei", 11))
        self._tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #fafafa;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 18px;
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

        basic_tab = self._create_basic_rules_tab()
        self._tab_widget.addTab(basic_tab, "基础规则")

        advanced_tab = self._create_advanced_rules_tab()
        self._tab_widget.addTab(advanced_tab, "高级规则")

        layout.addWidget(self._tab_widget)

        return panel

    def _create_basic_rules_tab(self) -> QWidget:
        """
        创建基础规则标签页
        """
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        prefix_group = self._create_prefix_group()
        layout.addWidget(prefix_group, 0, 0)

        suffix_group = self._create_suffix_group()
        layout.addWidget(suffix_group, 0, 1)

        replace_group = self._create_replace_group()
        layout.addWidget(replace_group, 1, 0, 1, 2)

        delete_group = self._create_delete_group()
        layout.addWidget(delete_group, 2, 0)

        insert_group = self._create_insert_group()
        layout.addWidget(insert_group, 2, 1)

        return widget

    def _create_prefix_group(self) -> QGroupBox:
        """
        创建前缀添加组
        """
        group = QGroupBox("添加前缀")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #666666;
            }
        """)

        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self._prefix_check = QCheckBox("启用")
        self._prefix_check.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #555555;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self._prefix_check.stateChanged.connect(self._on_rule_changed)

        self._prefix_input = QLineEdit()
        self._prefix_input.setPlaceholderText("输入前缀文本...")
        self._prefix_input.setFont(QFont("Microsoft YaHei", 11))
        self._prefix_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
                border-width: 2px;
            }
            QLineEdit:disabled {
                background-color: #f5f5f5;
            }
        """)
        self._prefix_input.textChanged.connect(self._on_rule_changed)

        input_layout.addWidget(QLabel("前缀:"))
        input_layout.addWidget(self._prefix_input)
        input_layout.addStretch()
        input_layout.addWidget(self._prefix_check)

        layout.addLayout(input_layout)

        return group

    def _create_suffix_group(self) -> QGroupBox:
        """
        创建后缀添加组
        """
        group = QGroupBox("添加后缀")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #666666;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self._suffix_check = QCheckBox("启用")
        self._suffix_check.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._suffix_check.stateChanged.connect(self._on_rule_changed)

        self._suffix_input = QLineEdit()
        self._suffix_input.setPlaceholderText("输入后缀文本...")
        self._suffix_input.setFont(QFont("Microsoft YaHei", 11))
        self._suffix_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
                border-width: 2px;
            }
            QLineEdit:disabled {
                background-color: #f5f5f5;
            }
        """)
        self._suffix_input.textChanged.connect(self._on_rule_changed)

        input_layout.addWidget(QLabel("后缀:"))
        input_layout.addWidget(self._suffix_input)
        input_layout.addStretch()
        input_layout.addWidget(self._suffix_check)
        layout.addLayout(input_layout)

        return group

    def _create_replace_group(self) -> QGroupBox:
        """
        创建替换组
        """
        group = QGroupBox("查找替换")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #666666;
            }
        """)
        layout = QHBoxLayout(group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        self._replace_check = QCheckBox("启用")
        self._replace_check.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._replace_check.stateChanged.connect(self._on_rule_changed)

        find_label = QLabel("查找:")
        self._find_input = QLineEdit()
        self._find_input.setPlaceholderText("查找内容...")
        self._find_input.setFont(QFont("Microsoft YaHei", 11))
        self._find_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
                border-width: 2px;
            }
            QLineEdit:disabled {
                background-color: #f5f5f5;
            }
        """)
        self._find_input.textChanged.connect(self._on_rule_changed)

        replace_label = QLabel("替换为:")
        self._replace_input = QLineEdit()
        self._replace_input.setPlaceholderText("替换内容...")
        self._replace_input.setFont(QFont("Microsoft YaHei", 11))
        self._replace_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
                border-width: 2px;
            }
            QLineEdit:disabled {
                background-color: #f5f5f5;
            }
        """)
        self._replace_input.textChanged.connect(self._on_rule_changed)

        self._replace_case_check = QCheckBox("区分大小写")
        self._replace_case_check.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._replace_case_check.stateChanged.connect(self._on_rule_changed)

        layout.addWidget(self._replace_check)
        layout.addWidget(find_label)
        layout.addWidget(self._find_input, 1)
        layout.addWidget(replace_label)
        layout.addWidget(self._replace_input, 1)
        layout.addWidget(self._replace_case_check)

        return group

    def _create_delete_group(self) -> QGroupBox:
        """
        创建删除组
        """
        group = QGroupBox("删除字符")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #666666;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        self._delete_check = QCheckBox("启用")
        self._delete_check.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._delete_check.stateChanged.connect(self._on_rule_changed)

        option_layout = QHBoxLayout()
        option_layout.setSpacing(8)

        self._delete_mode_group = QButtonGroup(self)
        self._delete_range_radio = QRadioButton("删除范围")
        self._delete_range_radio.setChecked(True)
        self._delete_range_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._delete_range_radio.toggled.connect(self._on_rule_changed)
        self._delete_text_radio = QRadioButton("删除文本")
        self._delete_text_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._delete_text_radio.toggled.connect(self._on_rule_changed)
        self._delete_mode_group.addButton(self._delete_range_radio)
        self._delete_mode_group.addButton(self._delete_text_radio)

        option_layout.addWidget(self._delete_check)
        option_layout.addWidget(self._delete_range_radio)
        option_layout.addWidget(self._delete_text_radio)
        option_layout.addStretch()

        range_layout = QHBoxLayout()
        range_layout.setSpacing(8)
        self._delete_start_label = QLabel("从第")
        self._delete_start_spin = QSpinBox()
        self._delete_start_spin.setRange(1, 999)
        self._delete_start_spin.setValue(1)
        self._delete_start_spin.setStyleSheet("""
            QSpinBox {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self._delete_start_spin.valueChanged.connect(self._on_rule_changed)

        self._delete_count_label = QLabel("个字符开始，删除")
        self._delete_count_spin = QSpinBox()
        self._delete_count_spin.setRange(1, 999)
        self._delete_count_spin.setValue(1)
        self._delete_count_spin.setStyleSheet("""
            QSpinBox {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self._delete_count_spin.valueChanged.connect(self._on_rule_changed)
        self._delete_char_label = QLabel("个字符")

        range_layout.addWidget(self._delete_start_label)
        range_layout.addWidget(self._delete_start_spin)
        range_layout.addWidget(self._delete_count_label)
        range_layout.addWidget(self._delete_count_spin)
        range_layout.addWidget(self._delete_char_label)
        range_layout.addStretch()

        text_layout = QHBoxLayout()
        text_layout.setSpacing(8)
        self._delete_text_label = QLabel("删除文本:")
        self._delete_text_input = QLineEdit()
        self._delete_text_input.setPlaceholderText("输入要删除的文本...")
        self._delete_text_input.setFont(QFont("Microsoft YaHei", 11))
        self._delete_text_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
                border-width: 2px;
            }
        """)
        self._delete_text_input.textChanged.connect(self._on_rule_changed)

        text_layout.addWidget(self._delete_text_label)
        text_layout.addWidget(self._delete_text_input, 1)

        layout.addLayout(option_layout)
        layout.addLayout(range_layout)
        layout.addLayout(text_layout)

        return group

    def _create_insert_group(self) -> QGroupBox:
        """
        创建插入组
        """
        group = QGroupBox("插入字符")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #666666;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        self._insert_check = QCheckBox("启用")
        self._insert_check.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._insert_check.stateChanged.connect(self._on_rule_changed)

        insert_layout = QHBoxLayout()
        insert_layout.setSpacing(8)

        self._insert_pos_label = QLabel("在第")
        self._insert_pos_spin = QSpinBox()
        self._insert_pos_spin.setRange(1, 999)
        self._insert_pos_spin.setValue(1)
        self._insert_pos_spin.setStyleSheet("""
            QSpinBox {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self._insert_pos_spin.valueChanged.connect(self._on_rule_changed)

        self._insert_text_label = QLabel("个字符位置插入:")
        self._insert_text_input = QLineEdit()
        self._insert_text_input.setPlaceholderText("输入要插入的文本...")
        self._insert_text_input.setFont(QFont("Microsoft YaHei", 11))
        self._insert_text_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
                border-width: 2px;
            }
        """)
        self._insert_text_input.textChanged.connect(self._on_rule_changed)

        insert_layout.addWidget(self._insert_check)
        insert_layout.addWidget(self._insert_pos_label)
        insert_layout.addWidget(self._insert_pos_spin)
        insert_layout.addWidget(self._insert_text_label)
        insert_layout.addWidget(self._insert_text_input, 1)

        layout.addLayout(insert_layout)

        return group

    def _create_advanced_rules_tab(self) -> QWidget:
        """
        创建高级规则标签页
        """
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        sequence_group = self._create_sequence_group()
        layout.addWidget(sequence_group, 0, 0)

        case_group = self._create_case_group()
        layout.addWidget(case_group, 0, 1)

        extension_group = self._create_extension_group()
        layout.addWidget(extension_group, 1, 0, 1, 2)

        return widget

    def _create_sequence_group(self) -> QGroupBox:
        """
        创建序列编号组
        """
        group = QGroupBox("序列编号")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #666666;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        self._sequence_check = QCheckBox("启用序列编号")
        self._sequence_check.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._sequence_check.stateChanged.connect(self._on_rule_changed)

        option_layout = QHBoxLayout()
        option_layout.setSpacing(10)

        start_label = QLabel("起始数字:")
        self._sequence_start_spin = QSpinBox()
        self._sequence_start_spin.setRange(0, 99999)
        self._sequence_start_spin.setValue(1)
        self._sequence_start_spin.setStyleSheet("""
            QSpinBox {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self._sequence_start_spin.valueChanged.connect(self._on_rule_changed)

        step_label = QLabel("步长:")
        self._sequence_step_spin = QSpinBox()
        self._sequence_step_spin.setRange(1, 999)
        self._sequence_step_spin.setValue(1)
        self._sequence_step_spin.setStyleSheet("""
            QSpinBox {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self._sequence_step_spin.valueChanged.connect(self._on_rule_changed)

        digits_label = QLabel("位数:")
        self._sequence_digits_spin = QSpinBox()
        self._sequence_digits_spin.setRange(1, 10)
        self._sequence_digits_spin.setValue(2)
        self._sequence_digits_spin.setStyleSheet("""
            QSpinBox {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self._sequence_digits_spin.valueChanged.connect(self._on_rule_changed)

        pos_label = QLabel("位置:")
        self._sequence_pos_combo = QComboBox()
        self._sequence_pos_combo.addItems(["前缀", "后缀"])
        self._sequence_pos_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self._sequence_pos_combo.currentIndexChanged.connect(self._on_rule_changed)

        separator_label = QLabel("分隔符:")
        self._sequence_separator_input = QLineEdit()
        self._sequence_separator_input.setText("_")
        self._sequence_separator_input.setMaximumWidth(60)
        self._sequence_separator_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self._sequence_separator_input.textChanged.connect(self._on_rule_changed)

        option_layout.addWidget(self._sequence_check)
        option_layout.addWidget(start_label)
        option_layout.addWidget(self._sequence_start_spin)
        option_layout.addWidget(step_label)
        option_layout.addWidget(self._sequence_step_spin)
        option_layout.addWidget(digits_label)
        option_layout.addWidget(self._sequence_digits_spin)
        option_layout.addWidget(pos_label)
        option_layout.addWidget(self._sequence_pos_combo)
        option_layout.addWidget(separator_label)
        option_layout.addWidget(self._sequence_separator_input)
        option_layout.addStretch()

        layout.addLayout(option_layout)

        return group

    def _create_case_group(self) -> QGroupBox:
        """
        创建大小写转换组
        """
        group = QGroupBox("大小写转换")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #666666;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        self._case_check = QCheckBox("启用大小写转换")
        self._case_check.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._case_check.stateChanged.connect(self._on_rule_changed)

        option_layout = QHBoxLayout()
        option_layout.setSpacing(10)

        self._case_mode_group = QButtonGroup(self)
        self._case_upper_radio = QRadioButton("全部大写")
        self._case_upper_radio.setChecked(True)
        self._case_upper_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._case_upper_radio.toggled.connect(self._on_rule_changed)

        self._case_lower_radio = QRadioButton("全部小写")
        self._case_lower_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._case_lower_radio.toggled.connect(self._on_rule_changed)

        self._case_capitalize_radio = QRadioButton("首字母大写")
        self._case_capitalize_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._case_capitalize_radio.toggled.connect(self._on_rule_changed)

        self._case_title_radio = QRadioButton("每个单词首字母大写")
        self._case_title_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._case_title_radio.toggled.connect(self._on_rule_changed)

        self._case_mode_group.addButton(self._case_upper_radio)
        self._case_mode_group.addButton(self._case_lower_radio)
        self._case_mode_group.addButton(self._case_capitalize_radio)
        self._case_mode_group.addButton(self._case_title_radio)

        option_layout.addWidget(self._case_check)
        option_layout.addWidget(self._case_upper_radio)
        option_layout.addWidget(self._case_lower_radio)
        option_layout.addWidget(self._case_capitalize_radio)
        option_layout.addWidget(self._case_title_radio)
        option_layout.addStretch()

        layout.addLayout(option_layout)

        return group

    def _create_extension_group(self) -> QGroupBox:
        """
        创建扩展名修改组
        """
        group = QGroupBox("扩展名修改")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #666666;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        self._extension_check = QCheckBox("启用扩展名修改")
        self._extension_check.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._extension_check.stateChanged.connect(self._on_rule_changed)

        option_layout = QHBoxLayout()
        option_layout.setSpacing(10)

        self._extension_mode_group = QButtonGroup(self)
        self._extension_change_radio = QRadioButton("修改为:")
        self._extension_change_radio.setChecked(True)
        self._extension_change_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._extension_change_radio.toggled.connect(self._on_rule_changed)

        self._extension_remove_radio = QRadioButton("移除扩展名")
        self._extension_remove_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._extension_remove_radio.toggled.connect(self._on_rule_changed)

        self._extension_mode_group.addButton(self._extension_change_radio)
        self._extension_mode_group.addButton(self._extension_remove_radio)

        self._extension_input = QLineEdit()
        self._extension_input.setPlaceholderText("例如: txt, jpg, pdf")
        self._extension_input.setMaximumWidth(100)
        self._extension_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self._extension_input.textChanged.connect(self._on_rule_changed)

        option_layout.addWidget(self._extension_check)
        option_layout.addWidget(self._extension_change_radio)
        option_layout.addWidget(self._extension_input)
        option_layout.addWidget(self._extension_remove_radio)
        option_layout.addStretch()

        self._include_dirs_check = QCheckBox("同时处理文件夹名称")
        self._include_dirs_check.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #555555;
            }
        """)
        self._include_dirs_check.stateChanged.connect(self._on_rule_changed)

        layout.addLayout(option_layout)
        layout.addWidget(self._include_dirs_check)

        return group

    def _create_files_panel(self) -> QWidget:
        """
        创建文件列表面板
        """
        panel = QGroupBox("文件列表")
        panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #1565C0;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(10)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)

        add_files_btn = QPushButton("📁 添加文件")
        add_files_btn.setMinimumWidth(100)
        add_files_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        add_files_btn.clicked.connect(self._on_add_files)

        add_folder_btn = QPushButton("📂 添加文件夹")
        add_folder_btn.setMinimumWidth(100)
        add_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
        """)
        add_folder_btn.clicked.connect(self._on_add_folder)

        clear_btn = QPushButton("🗑️ 清空列表")
        clear_btn.setMinimumWidth(100)
        clear_btn.setStyleSheet("""
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
        clear_btn.clicked.connect(self._on_clear_files)

        remove_selected_btn = QPushButton("✖️ 移除选中")
        remove_selected_btn.setMinimumWidth(100)
        remove_selected_btn.setStyleSheet("""
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
        remove_selected_btn.clicked.connect(self._on_remove_selected)

        toolbar_layout.addWidget(add_files_btn)
        toolbar_layout.addWidget(add_folder_btn)
        toolbar_layout.addWidget(remove_selected_btn)
        toolbar_layout.addWidget(clear_btn)
        toolbar_layout.addStretch()

        layout.addLayout(toolbar_layout)

        self._files_table = QTableWidget()
        self._files_table.setColumnCount(4)
        self._files_table.setHorizontalHeaderLabels(["原文件名", "新文件名", "类型", "状态"])
        self._files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._files_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self._files_table.setAlternatingRowColors(True)
        self._files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._files_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._files_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._files_table.setColumnWidth(2, 80)
        self._files_table.setColumnWidth(3, 100)
        self._files_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565C0;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)
        self._files_table.setFont(QFont("Microsoft YaHei", 10))

        layout.addWidget(self._files_table, 1)

        return panel

    def _create_action_bar(self) -> QHBoxLayout:
        """
        创建操作栏
        """
        layout = QHBoxLayout()
        layout.setSpacing(10)

        layout.addStretch()

        self._preview_btn = QPushButton("👁️ 预览重命名")
        self._preview_btn.setMinimumWidth(120)
        self._preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #6A1B9A;
            }
        """)
        self._preview_btn.clicked.connect(self._on_preview)

        self._execute_btn = QPushButton("⚡ 执行重命名")
        self._execute_btn.setMinimumWidth(120)
        self._execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self._execute_btn.clicked.connect(self._on_execute)

        self._undo_btn = QPushButton("↩️ 撤销")
        self._undo_btn.setMinimumWidth(100)
        self._undo_btn.setEnabled(False)
        self._undo_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
            QPushButton:pressed {
                background-color: #37474F;
            }
            QPushButton:disabled {
                background-color: #90A4AE;
            }
        """)
        self._undo_btn.clicked.connect(self._on_undo)

        layout.addWidget(self._preview_btn)
        layout.addWidget(self._execute_btn)
        layout.addWidget(self._undo_btn)

        return layout

    def _on_rule_changed(self):
        """
        当规则变化时触发，自动更新预览
        """
        if self._files:
            self._update_preview()

    def _on_add_files(self):
        """
        添加文件按钮点击事件
        """
        file_paths, _ = QFileDialog.getOpenFileNames(
            None, "选择文件", "", "所有文件 (*.*)"
        )
        if file_paths:
            for file_path in file_paths:
                if not any(f.original_path == file_path for f in self._files):
                    file_name = os.path.basename(file_path)
                    is_dir = os.path.isdir(file_path)
                    size = 0
                    try:
                        if not is_dir:
                            size = os.path.getsize(file_path)
                    except:
                        pass

                    file_item = FileItem(
                        original_name=file_name,
                        original_path=file_path,
                        is_directory=is_dir,
                        size=size,
                        new_name=file_name
                    )
                    self._files.append(file_item)

            self._update_files_table()
            self._update_file_count()

    def _on_add_folder(self):
        """
        添加文件夹按钮点击事件
        """
        folder_path = QFileDialog.getExistingDirectory(None, "选择文件夹")
        if folder_path:
            if not any(f.original_path == folder_path for f in self._files):
                folder_name = os.path.basename(folder_path)
                file_item = FileItem(
                    original_name=folder_name,
                    original_path=folder_path,
                    is_directory=True,
                    new_name=folder_name
                )
                self._files.append(file_item)
                self._update_files_table()
                self._update_file_count()

    def _on_clear_files(self):
        """
        清空文件列表
        """
        if not self._files:
            return

        reply = QMessageBox.question(
            None, "确认清空",
            f"确定要清空列表中的 {len(self._files)} 个文件/文件夹吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._files = []
            self._update_files_table()
            self._update_file_count()

    def _on_remove_selected(self):
        """
        移除选中的文件
        """
        selected_rows = set()
        for item in self._files_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.information(None, "提示", "请先选择要移除的文件！")
            return

        selected_rows = sorted(selected_rows, reverse=True)
        for row in selected_rows:
            if row < len(self._files):
                del self._files[row]

        self._update_files_table()
        self._update_file_count()

    def _update_files_table(self):
        """
        更新文件表格
        """
        self._files_table.setRowCount(len(self._files))

        for i, file_item in enumerate(self._files):
            original_item = QTableWidgetItem(file_item.original_name)
            original_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self._files_table.setItem(i, 0, original_item)

            new_name = file_item.new_name if file_item.new_name else file_item.original_name
            new_item = QTableWidgetItem(new_name)
            new_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

            if new_name != file_item.original_name:
                new_item.setForeground(QBrush(QColor("#1565C0")))
                new_item.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))

            self._files_table.setItem(i, 1, new_item)

            type_text = "文件夹" if file_item.is_directory else "文件"
            type_item = QTableWidgetItem(type_text)
            type_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._files_table.setItem(i, 2, type_item)

            status_text = "待处理"
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._files_table.setItem(i, 3, status_item)

    def _update_file_count(self):
        """
        更新文件计数
        """
        file_count = sum(1 for f in self._files if not f.is_directory)
        dir_count = sum(1 for f in self._files if f.is_directory)

        count_text = f"已选择: {len(self._files)} 个"
        if file_count > 0:
            count_text += f" (文件: {file_count}"
        if dir_count > 0:
            if file_count > 0:
                count_text += ", "
            else:
                count_text += " ("
            count_text += f"文件夹: {dir_count}"
        if file_count > 0 or dir_count > 0:
            count_text += ")"

        self._file_count_label.setText(count_text)

    def _collect_rules(self) -> List[RenameRule]:
        """
        收集当前设置的所有规则
        """
        rules = []

        if self._prefix_check.isChecked() and self._prefix_input.text().strip():
            rules.append(RenameRule(
                rule_type=RenameRuleType.ADD_PREFIX,
                parameters={"text": self._prefix_input.text()}
            ))

        if self._suffix_check.isChecked() and self._suffix_input.text().strip():
            rules.append(RenameRule(
                rule_type=RenameRuleType.ADD_SUFFIX,
                parameters={"text": self._suffix_input.text()}
            ))

        if self._replace_check.isChecked():
            find_text = self._find_input.text()
            if find_text:
                rules.append(RenameRule(
                    rule_type=RenameRuleType.REPLACE,
                    parameters={
                        "find": find_text,
                        "replace": self._replace_input.text(),
                        "case_sensitive": self._replace_case_check.isChecked()
                    }
                ))

        if self._delete_check.isChecked():
            if self._delete_range_radio.isChecked():
                rules.append(RenameRule(
                    rule_type=RenameRuleType.DELETE,
                    parameters={
                        "mode": "range",
                        "start": self._delete_start_spin.value(),
                        "count": self._delete_count_spin.value()
                    }
                ))
            elif self._delete_text_radio.isChecked() and self._delete_text_input.text():
                rules.append(RenameRule(
                    rule_type=RenameRuleType.DELETE,
                    parameters={
                        "mode": "text",
                        "text": self._delete_text_input.text()
                    }
                ))

        if self._insert_check.isChecked() and self._insert_text_input.text():
            rules.append(RenameRule(
                rule_type=RenameRuleType.INSERT,
                parameters={
                    "position": self._insert_pos_spin.value(),
                    "text": self._insert_text_input.text()
                }
            ))

        if self._sequence_check.isChecked():
            rules.append(RenameRule(
                rule_type=RenameRuleType.SEQUENCE,
                parameters={
                    "start": self._sequence_start_spin.value(),
                    "step": self._sequence_step_spin.value(),
                    "digits": self._sequence_digits_spin.value(),
                    "position": "prefix" if self._sequence_pos_combo.currentText() == "前缀" else "suffix",
                    "separator": self._sequence_separator_input.text()
                }
            ))

        if self._case_check.isChecked():
            case_type = CaseChangeType.UPPER
            if self._case_lower_radio.isChecked():
                case_type = CaseChangeType.LOWER
            elif self._case_capitalize_radio.isChecked():
                case_type = CaseChangeType.CAPITALIZE
            elif self._case_title_radio.isChecked():
                case_type = CaseChangeType.TITLE

            rules.append(RenameRule(
                rule_type=RenameRuleType.CASE_CHANGE,
                parameters={"case_type": case_type}
            ))

        if self._extension_check.isChecked():
            if self._extension_remove_radio.isChecked():
                rules.append(RenameRule(
                    rule_type=RenameRuleType.EXTENSION_CHANGE,
                    parameters={
                        "mode": "remove",
                        "include_dirs": self._include_dirs_check.isChecked()
                    }
                ))
            else:
                extension = self._extension_input.text().strip().lstrip('.')
                if extension:
                    rules.append(RenameRule(
                        rule_type=RenameRuleType.EXTENSION_CHANGE,
                        parameters={
                            "mode": "change",
                            "extension": extension,
                            "include_dirs": self._include_dirs_check.isChecked()
                        }
                    ))

        return rules

    def _apply_rules_to_name(self, name: str, rules: List[RenameRule], is_dir: bool,
                             sequence_index: int = 0) -> str:
        """
        对文件名应用所有规则
        """
        base_name, extension = os.path.splitext(name)
        result = base_name

        for rule in rules:
            if rule.rule_type == RenameRuleType.ADD_PREFIX:
                result = rule.parameters["text"] + result

            elif rule.rule_type == RenameRuleType.ADD_SUFFIX:
                result = result + rule.parameters["text"]

            elif rule.rule_type == RenameRuleType.REPLACE:
                find_text = rule.parameters["find"]
                replace_text = rule.parameters["replace"]
                case_sensitive = rule.parameters["case_sensitive"]

                if case_sensitive:
                    result = result.replace(find_text, replace_text)
                else:
                    pattern = re.escape(find_text)
                    result = re.sub(pattern, replace_text, result, flags=re.IGNORECASE)

            elif rule.rule_type == RenameRuleType.DELETE:
                if rule.parameters["mode"] == "range":
                    start = rule.parameters["start"] - 1
                    count = rule.parameters["count"]
                    if start < len(result):
                        result = result[:start] + result[start + count:]
                elif rule.parameters["mode"] == "text":
                    result = result.replace(rule.parameters["text"], "")

            elif rule.rule_type == RenameRuleType.INSERT:
                position = rule.parameters["position"] - 1
                text = rule.parameters["text"]
                if position <= len(result):
                    result = result[:position] + text + result[position:]
                else:
                    result = result + text

            elif rule.rule_type == RenameRuleType.SEQUENCE:
                start = rule.parameters["start"]
                step = rule.parameters["step"]
                digits = rule.parameters["digits"]
                position = rule.parameters["position"]
                separator = rule.parameters["separator"]

                seq_num = start + sequence_index * step
                seq_str = str(seq_num).zfill(digits)

                if position == "prefix":
                    result = seq_str + separator + result
                else:
                    result = result + separator + seq_str

            elif rule.rule_type == RenameRuleType.CASE_CHANGE:
                case_type = rule.parameters["case_type"]
                if case_type == CaseChangeType.UPPER:
                    result = result.upper()
                elif case_type == CaseChangeType.LOWER:
                    result = result.lower()
                elif case_type == CaseChangeType.CAPITALIZE:
                    result = result.capitalize()
                elif case_type == CaseChangeType.TITLE:
                    result = result.title()

            elif rule.rule_type == RenameRuleType.EXTENSION_CHANGE:
                if is_dir and not rule.parameters["include_dirs"]:
                    continue

                if rule.parameters["mode"] == "remove":
                    extension = ""
                elif rule.parameters["mode"] == "change":
                    extension = "." + rule.parameters["extension"]

        if result:
            return result + extension
        else:
            return extension

    def _update_preview(self):
        """
        更新预览
        """
        rules = self._collect_rules()

        sequence_index = 0
        for file_item in self._files:
            file_item.new_name = self._apply_rules_to_name(
                file_item.original_name,
                rules,
                file_item.is_directory,
                sequence_index
            )

            if not file_item.is_directory:
                sequence_index += 1

        self._update_files_table()

    def _on_preview(self):
        """
        预览按钮点击事件
        """
        if not self._files:
            QMessageBox.warning(None, "警告", "请先添加文件！")
            return

        rules = self._collect_rules()
        if not rules:
            QMessageBox.warning(None, "警告", "请先设置至少一个重命名规则！")
            return

        self._update_preview()

        changed_count = sum(1 for f in self._files if f.new_name != f.original_name)
        if changed_count > 0:
            QMessageBox.information(
                None, "预览完成",
                f"预览完成！有 {changed_count} 个文件/文件夹将被重命名。\n"
                f"请在列表中查看新文件名（蓝色显示）。"
            )
        else:
            QMessageBox.information(
                None, "预览完成",
                "所有文件名都不会改变，请调整重命名规则。"
            )

    def _on_execute(self):
        """
        执行重命名
        """
        if not self._files:
            QMessageBox.warning(None, "警告", "请先添加文件！")
            return

        rules = self._collect_rules()
        if not rules:
            QMessageBox.warning(None, "警告", "请先设置至少一个重命名规则！")
            return

        self._update_preview()

        rename_operations = []
        for file_item in self._files:
            if file_item.new_name != file_item.original_name:
                dir_path = os.path.dirname(file_item.original_path)
                new_path = os.path.join(dir_path, file_item.new_name)

                if new_path != file_item.original_path:
                    rename_operations.append(RenameHistory(
                        original_path=file_item.original_path,
                        new_path=new_path,
                        original_name=file_item.original_name,
                        new_name=file_item.new_name
                    ))

        if not rename_operations:
            QMessageBox.information(
                None, "提示",
                "没有需要重命名的文件/文件夹，请调整规则。"
            )
            return

        reply = QMessageBox.question(
            None, "确认执行",
            f"确定要重命名 {len(rename_operations)} 个文件/文件夹吗？\n\n"
            f"此操作可以通过'撤销'按钮撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self._execute_btn.setEnabled(False)
        self._preview_btn.setEnabled(False)

        self._worker = FileRenamerWorker(rename_operations)
        self._worker.progress.connect(self._on_rename_progress)
        self._worker.finished.connect(self._on_rename_finished)
        self._worker.start()

    def _on_rename_progress(self, current: int, total: int):
        """
        重命名进度更新
        """
        self._execute_btn.setText(f"处理中... {current}/{total}")

    def _on_rename_finished(self, success: bool, count: int, errors: List[str]):
        """
        重命名完成
        """
        self._execute_btn.setEnabled(True)
        self._preview_btn.setEnabled(True)
        self._execute_btn.setText("⚡ 执行重命名")

        if errors:
            error_msg = "\n".join(errors[:10])
            if len(errors) > 10:
                error_msg += f"\n... 还有 {len(errors) - 10} 个错误"
            QMessageBox.warning(
                None, "部分失败",
                f"成功重命名 {count} 个文件/文件夹。\n"
                f"失败 {len(errors)} 个：\n{error_msg}"
            )
        else:
            QMessageBox.information(
                None, "完成",
                f"成功重命名 {count} 个文件/文件夹！"
            )

        if self._worker.history:
            self._rename_history.append(self._worker.history)
            self._undo_btn.setEnabled(True)

        for op in self._worker.history:
            for file_item in self._files:
                if file_item.original_path == op.original_path:
                    file_item.original_path = op.new_path
                    file_item.original_name = op.new_name
                    file_item.new_name = op.new_name
                    break

        self._update_files_table()

    def _on_undo(self):
        """
        撤销上次重命名操作
        """
        if not self._rename_history:
            QMessageBox.information(None, "提示", "没有可撤销的操作。")
            return

        last_operations = self._rename_history.pop()
        if not last_operations:
            return

        success_count = 0
        errors = []

        for op in reversed(last_operations):
            try:
                if os.path.exists(op.original_path):
                    raise FileExistsError(f"目标文件已存在: {op.original_name}")
                os.rename(op.new_path, op.original_path)

                for file_item in self._files:
                    if file_item.original_path == op.new_path:
                        file_item.original_path = op.original_path
                        file_item.original_name = op.original_name
                        file_item.new_name = op.original_name
                        break

                success_count += 1
            except Exception as e:
                errors.append(f"{op.new_name}: {str(e)}")

        if errors:
            error_msg = "\n".join(errors[:5])
            QMessageBox.warning(
                None, "部分撤销失败",
                f"成功撤销 {success_count} 个重命名操作。\n"
                f"失败 {len(errors)} 个：\n{error_msg}"
            )
        else:
            QMessageBox.information(
                None, "撤销完成",
                f"成功撤销 {success_count} 个重命名操作！"
            )

        if not self._rename_history:
            self._undo_btn.setEnabled(False)

        self._update_files_table()
