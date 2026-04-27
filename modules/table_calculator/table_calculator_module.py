#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表格计算器模块
提供表格数据计算和历史记录功能
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLabel, QSplitter,
                             QListWidget, QListWidgetItem, QMessageBox, QHeaderView,
                             QSpinBox, QComboBox, QGroupBox, QFrame)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont, QColor

from modules.module_manager import BaseModule
from database.database_manager import DatabaseManager


class TableCalculatorModule(BaseModule):
    """
    表格计算器模块
    提供表格数据计算和历史记录功能
    """
    
    @property
    def module_id(self) -> str:
        return "table_calculator"
    
    @property
    def name(self) -> str:
        return "表格计算器"
    
    @property
    def description(self) -> str:
        return "一个功能强大的表格计算器，支持多种计算操作和历史记录"
    
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
        self._create_history_table()
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        pass
    
    def _create_history_table(self):
        """
        创建计算历史记录表
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS calculation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL,
            expression TEXT,
            result TEXT NOT NULL,
            row_count INTEGER,
            col_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self._db.execute(create_table_sql)
    
    def _create_widget(self) -> QWidget:
        """
        创建表格计算器的主界面
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        calculator_panel = self._create_calculator_panel()
        content_splitter.addWidget(calculator_panel)
        
        history_panel = self._create_history_panel()
        content_splitter.addWidget(history_panel)
        
        content_splitter.setSizes([700, 300])
        
        main_layout.addWidget(content_splitter, 1)
        
        self._load_history()
        
        return widget
    
    def _create_toolbar(self) -> QWidget:
        """
        创建工具栏
        """
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        table_size_group = QGroupBox("表格大小")
        table_size_layout = QHBoxLayout(table_size_group)
        table_size_layout.setSpacing(10)
        
        row_label = QLabel("行数:")
        table_size_layout.addWidget(row_label)
        
        self.row_spin = QSpinBox()
        self.row_spin.setRange(1, 100)
        self.row_spin.setValue(5)
        self.row_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        table_size_layout.addWidget(self.row_spin)
        
        col_label = QLabel("列数:")
        table_size_layout.addWidget(col_label)
        
        self.col_spin = QSpinBox()
        self.col_spin.setRange(1, 20)
        self.col_spin.setValue(3)
        self.col_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        table_size_layout.addWidget(self.col_spin)
        
        resize_btn = QPushButton("调整大小")
        resize_btn.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        resize_btn.clicked.connect(self._on_resize_table)
        table_size_layout.addWidget(resize_btn)
        
        layout.addWidget(table_size_group)
        
        quick_ops_group = QGroupBox("快速计算")
        quick_ops_layout = QHBoxLayout(quick_ops_group)
        quick_ops_layout.setSpacing(8)
        
        sum_btn = QPushButton("求和")
        sum_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
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
        sum_btn.clicked.connect(lambda: self._on_calculate('sum'))
        quick_ops_layout.addWidget(sum_btn)
        
        avg_btn = QPushButton("平均值")
        avg_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 6px 12px;
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
        avg_btn.clicked.connect(lambda: self._on_calculate('average'))
        quick_ops_layout.addWidget(avg_btn)
        
        max_btn = QPushButton("最大值")
        max_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 6px 12px;
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
        max_btn.clicked.connect(lambda: self._on_calculate('max'))
        quick_ops_layout.addWidget(max_btn)
        
        min_btn = QPushButton("最小值")
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: #E91E63;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C2185B;
            }
            QPushButton:pressed {
                background-color: #AD1457;
            }
        """)
        min_btn.clicked.connect(lambda: self._on_calculate('min'))
        quick_ops_layout.addWidget(min_btn)
        
        count_btn = QPushButton("计数")
        count_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0097A7;
            }
            QPushButton:pressed {
                background-color: #00838F;
            }
        """)
        count_btn.clicked.connect(lambda: self._on_calculate('count'))
        quick_ops_layout.addWidget(count_btn)
        
        layout.addWidget(quick_ops_group)
        
        layout.addStretch()
        
        clear_btn = QPushButton("清空表格")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 6px 12px;
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
        clear_btn.clicked.connect(self._on_clear_table)
        layout.addWidget(clear_btn)
        
        return toolbar
    
    def _create_calculator_panel(self) -> QWidget:
        """
        创建计算器面板
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        table_label = QLabel("数据表格")
        table_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        table_label.setStyleSheet("color: #333;")
        layout.addWidget(table_label)
        
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(5)
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels([f"列 {i+1}" for i in range(3)])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_widget.verticalHeader().setDefaultSectionSize(30)
        self.table_widget.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                gridline-color: #e0e0e0;
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
                padding: 5px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table_widget, 1)
        
        result_frame = QFrame()
        result_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        result_frame.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        result_layout = QHBoxLayout(result_frame)
        result_layout.setContentsMargins(10, 10, 10, 10)
        
        result_label = QLabel("计算结果:")
        result_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        result_label.setStyleSheet("color: #333;")
        result_layout.addWidget(result_label)
        
        self.result_display = QLabel("-")
        self.result_display.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        self.result_display.setStyleSheet("color: #1565C0;")
        result_layout.addWidget(self.result_display)
        
        result_layout.addStretch()
        
        save_result_btn = QPushButton("保存结果")
        save_result_btn.setStyleSheet("""
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
        save_result_btn.clicked.connect(self._on_save_result)
        result_layout.addWidget(save_result_btn)
        
        layout.addWidget(result_frame)
        
        return panel
    
    def _create_history_panel(self) -> QWidget:
        """
        创建历史记录面板
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        history_label = QLabel("计算历史")
        history_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        history_label.setStyleSheet("color: #333;")
        layout.addWidget(history_label)
        
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                padding: 2px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565C0;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.history_list.currentRowChanged.connect(self._on_history_selected)
        layout.addWidget(self.history_list, 1)
        
        clear_history_btn = QPushButton("清空历史")
        clear_history_btn.setStyleSheet("""
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
        clear_history_btn.clicked.connect(self._on_clear_history)
        layout.addWidget(clear_history_btn)
        
        return panel
    
    def _on_resize_table(self):
        """
        调整表格大小
        """
        rows = self.row_spin.value()
        cols = self.col_spin.value()
        
        self.table_widget.setRowCount(rows)
        self.table_widget.setColumnCount(cols)
        self.table_widget.setHorizontalHeaderLabels([f"列 {i+1}" for i in range(cols)])
        
        self.statusBar().showMessage(f"表格已调整为 {rows} 行 x {cols} 列")
    
    def _on_calculate(self, operation: str):
        """
        执行计算操作
        """
        values = []
        
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item and item.text().strip():
                    try:
                        value = float(item.text().strip())
                        values.append(value)
                    except ValueError:
                        pass
        
        if not values:
            QMessageBox.warning(None, "警告", "请在表格中输入至少一个数字！")
            return
        
        result = None
        operation_name = ""
        
        if operation == 'sum':
            result = sum(values)
            operation_name = "求和"
        elif operation == 'average':
            result = sum(values) / len(values)
            operation_name = "平均值"
        elif operation == 'max':
            result = max(values)
            operation_name = "最大值"
        elif operation == 'min':
            result = min(values)
            operation_name = "最小值"
        elif operation == 'count':
            result = len(values)
            operation_name = "计数"
        
        if result is not None:
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            
            self.result_display.setText(str(result))
            self._last_operation = operation_name
            self._last_result = result
            self._last_values = values
            
            self.statusBar().showMessage(f"{operation_name}计算完成: {result}")
    
    def _on_save_result(self):
        """
        保存计算结果到历史记录
        """
        if not hasattr(self, '_last_result') or self._last_result is None:
            QMessageBox.warning(None, "警告", "请先执行一次计算！")
            return
        
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        history_id = self._db.insert('calculation_history', {
            'operation': self._last_operation,
            'expression': f"共 {len(self._last_values)} 个数值",
            'result': str(self._last_result),
            'row_count': self.table_widget.rowCount(),
            'col_count': self.table_widget.columnCount(),
            'created_at': now
        })
        
        if history_id > 0:
            self._load_history()
            QMessageBox.information(None, "成功", "计算结果已保存到历史记录！")
    
    def _on_clear_table(self):
        """
        清空表格
        """
        reply = QMessageBox.question(
            None, "确认清空",
            "确定要清空表格中的所有数据吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.table_widget.clearContents()
            self.result_display.setText("-")
            self._last_operation = None
            self._last_result = None
            self._last_values = None
            self.statusBar().showMessage("表格已清空")
    
    def _on_clear_history(self):
        """
        清空历史记录
        """
        reply = QMessageBox.question(
            None, "确认清空",
            "确定要清空所有计算历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._db.delete('calculation_history', '1=1')
            self._load_history()
            self.statusBar().showMessage("历史记录已清空")
    
    def _on_history_selected(self, index):
        """
        当选择历史记录时触发
        """
        if index < 0:
            return
        
        item = self.history_list.item(index)
        history_id = item.data(Qt.ItemDataRole.UserRole)
        
        history = self._db.query_one(
            "SELECT * FROM calculation_history WHERE id = ?",
            (history_id,)
        )
        
        if history:
            self.result_display.setText(history['result'])
            self.statusBar().showMessage(f"已加载历史记录: {history['operation']} = {history['result']}")
    
    def _load_history(self):
        """
        加载历史记录
        """
        self.history_list.clear()
        
        histories = self._db.query_all(
            "SELECT id, operation, result, created_at FROM calculation_history ORDER BY created_at DESC"
        )
        
        for history in histories:
            item_text = f"{history['operation']}: {history['result']}\n{history['created_at']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, history['id'])
            self.history_list.addItem(item)
    
    def statusBar(self):
        """
        模拟QMainWindow的statusBar方法
        """
        return type('StatusBar', (), {
            'showMessage': lambda msg: print(f"[表格计算器] {msg}")
        })()
