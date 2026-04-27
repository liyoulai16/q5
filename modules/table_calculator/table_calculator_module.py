#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表格计算器模块
提供传统计算器样式的表格按钮布局和历史记录弹窗功能
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QDialog, QListWidget,
                             QListWidgetItem, QMessageBox, QSplitter, QSizePolicy,
                             QSpacerItem)
from PyQt6.QtCore import Qt, QDateTime, QSize
from PyQt6.QtGui import QFont, QColor, QPalette

from modules.module_manager import BaseModule
from database.database_manager import DatabaseManager


class HistoryDialog(QDialog):
    """
    历史记录弹窗对话框
    """
    
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.setWindowTitle("计算历史记录")
        self.setMinimumSize(500, 400)
        self.resize(550, 500)
        self._db = db_manager
        
        self._init_ui()
        self._load_history()
    
    def _init_ui(self):
        """
        初始化界面
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        title_label = QLabel("计算历史记录")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        layout.addWidget(title_label)
        
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                padding: 5px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f0f0f0;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565C0;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.history_list, 1)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        copy_btn = QPushButton("复制选中结果")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        copy_btn.clicked.connect(self._on_copy_selected)
        button_layout.addWidget(copy_btn)
        
        clear_btn = QPushButton("清空历史记录")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        clear_btn.clicked.connect(self._on_clear_history)
        button_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_history(self):
        """
        加载历史记录
        """
        self.history_list.clear()
        
        histories = self._db.query_all(
            "SELECT id, operation, expression, result, created_at FROM calculation_history ORDER BY created_at DESC"
        )
        
        for history in histories:
            item_text = f"操作: {history['operation']}\n表达式: {history['expression']}\n结果: {history['result']}\n时间: {history['created_at']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, history['id'])
            item.setData(Qt.ItemDataRole.UserRole + 1, history['result'])
            self.history_list.addItem(item)
    
    def _on_copy_selected(self):
        """
        复制选中的结果
        """
        current_row = self.history_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择一条历史记录！")
            return
        
        item = self.history_list.item(current_row)
        result = item.data(Qt.ItemDataRole.UserRole + 1)
        
        clipboard = self.parent().window().clipboard() if self.parent() else None
        if clipboard:
            clipboard.setText(str(result))
        
        QMessageBox.information(self, "成功", f"结果 '{result}' 已复制到剪贴板！")
    
    def _on_clear_history(self):
        """
        清空历史记录
        """
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有计算历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._db.delete('calculation_history', '1=1')
            self._load_history()
            QMessageBox.information(self, "成功", "历史记录已清空！")


class TableCalculatorModule(BaseModule):
    """
    表格计算器模块
    提供传统计算器样式的表格按钮布局和历史记录弹窗功能
    """
    
    @property
    def module_id(self) -> str:
        return "table_calculator"
    
    @property
    def name(self) -> str:
        return "表格计算器"
    
    @property
    def description(self) -> str:
        return "传统计算器样式的表格按钮计算器，支持历史记录弹窗查看"
    
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
        self._reset_calculator()
    
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self._db.execute(create_table_sql)
    
    def _reset_calculator(self):
        """
        重置计算器状态
        """
        self._current_input = "0"
        self._previous_value = None
        self._operator = None
        self._waiting_for_operand = False
        self._last_expression = ""
    
    def _create_widget(self) -> QWidget:
        """
        创建表格计算器的主界面
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        title_label = QLabel("表格计算器")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        display_frame = QFrame()
        display_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        display_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        display_layout = QVBoxLayout(display_frame)
        display_layout.setContentsMargins(15, 15, 15, 15)
        display_layout.setSpacing(5)
        
        self.expression_label = QLabel("")
        self.expression_label.setFont(QFont("Microsoft YaHei", 12))
        self.expression_label.setStyleSheet("color: #666;")
        self.expression_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        display_layout.addWidget(self.expression_label)
        
        self.display_label = QLabel("0")
        self.display_label.setFont(QFont("Microsoft YaHei", 32, QFont.Weight.Bold))
        self.display_label.setStyleSheet("color: #333;")
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        display_layout.addWidget(self.display_label)
        
        main_layout.addWidget(display_frame)
        
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        grid_layout = QGridLayout(buttons_frame)
        grid_layout.setContentsMargins(15, 15, 15, 15)
        grid_layout.setSpacing(10)
        
        button_style = """
            QPushButton {
                background-color: #f5f5f5;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #bdbdbd;
            }
        """
        
        operator_style = """
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #EF6C00;
            }
        """
        
        equal_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """
        
        clear_style = """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """
        
        history_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """
        
        buttons = [
            ('C', 0, 0, clear_style),
            ('±', 0, 1, button_style),
            ('%', 0, 2, button_style),
            ('÷', 0, 3, operator_style),
            ('历史', 0, 4, history_style),
            
            ('7', 1, 0, button_style),
            ('8', 1, 1, button_style),
            ('9', 1, 2, button_style),
            ('×', 1, 3, operator_style),
            ('(', 1, 4, button_style),
            
            ('4', 2, 0, button_style),
            ('5', 2, 1, button_style),
            ('6', 2, 2, button_style),
            ('-', 2, 3, operator_style),
            (')', 2, 4, button_style),
            
            ('1', 3, 0, button_style),
            ('2', 3, 1, button_style),
            ('3', 3, 2, button_style),
            ('+', 3, 3, operator_style),
            ('=', 3, 4, equal_style, 2, 1),
            
            ('0', 4, 0, button_style, 1, 2),
            ('.', 4, 2, button_style),
        ]
        
        self._button_widgets = {}
        
        for button_info in buttons:
            if len(button_info) == 4:
                text, row, col, style = button_info
                row_span, col_span = 1, 1
            elif len(button_info) == 6:
                text, row, col, style, row_span, col_span = button_info
            
            btn = QPushButton(text)
            btn.setStyleSheet(style)
            btn.setMinimumSize(60, 60)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            if text == '历史':
                btn.clicked.connect(self._on_show_history)
            elif text == '=':
                btn.clicked.connect(self._on_calculate)
            elif text == 'C':
                btn.clicked.connect(self._on_clear)
            elif text == '±':
                btn.clicked.connect(self._on_toggle_sign)
            elif text == '%':
                btn.clicked.connect(self._on_percent)
            elif text in ['+', '-', '×', '÷']:
                btn.clicked.connect(lambda checked, op=text: self._on_operator(op))
            else:
                btn.clicked.connect(lambda checked, t=text: self._on_input(t))
            
            grid_layout.addWidget(btn, row, col, row_span, col_span)
            self._button_widgets[text] = btn
        
        main_layout.addWidget(buttons_frame, 1)
        
        info_label = QLabel("提示: 点击按钮进行计算，点击'历史'查看计算记录")
        info_label.setFont(QFont("Microsoft YaHei", 10))
        info_label.setStyleSheet("color: #666;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)
        
        return widget
    
    def _on_input(self, value):
        """
        处理数字和小数点输入
        """
        if self._waiting_for_operand:
            self._current_input = "0"
            self._waiting_for_operand = False
        
        if value == '.':
            if '.' in self._current_input:
                return
            self._current_input += '.'
        else:
            if self._current_input == "0" and value != '.':
                self._current_input = value
            else:
                self._current_input += value
        
        self._update_display()
    
    def _on_operator(self, operator):
        """
        处理运算符输入
        """
        try:
            current_value = float(self._current_input)
        except ValueError:
            current_value = 0
        
        if self._previous_value is None:
            self._previous_value = current_value
        else:
            if self._operator:
                result = self._perform_calculation(self._previous_value, current_value, self._operator)
                self._current_input = str(result)
                self._previous_value = result
                self._update_display()
        
        self._operator = operator
        self._waiting_for_operand = True
        
        op_symbol = {'+': '+', '-': '-', '×': '×', '÷': '÷'}[operator]
        self._last_expression = f"{self._previous_value} {op_symbol}"
        self.expression_label.setText(self._last_expression)
    
    def _on_calculate(self):
        """
        执行计算
        """
        if self._operator is None or self._previous_value is None:
            return
        
        try:
            current_value = float(self._current_input)
        except ValueError:
            current_value = 0
        
        op_symbol = {'+': '+', '-': '-', '×': '×', '÷': '÷'}[self._operator]
        expression = f"{self._previous_value} {op_symbol} {current_value}"
        
        result = self._perform_calculation(self._previous_value, current_value, self._operator)
        
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        
        self._current_input = str(result)
        self._last_expression = f"{expression} = {result}"
        self.expression_label.setText(self._last_expression)
        self._update_display()
        
        self._save_to_history("基本计算", expression, str(result))
        
        self._previous_value = None
        self._operator = None
        self._waiting_for_operand = True
    
    def _perform_calculation(self, a, b, operator):
        """
        执行具体的计算操作
        """
        if operator == '+':
            return a + b
        elif operator == '-':
            return a - b
        elif operator == '×':
            return a * b
        elif operator == '÷':
            if b == 0:
                QMessageBox.warning(None, "错误", "除数不能为零！")
                return a
            return a / b
        return b
    
    def _on_clear(self):
        """
        清空计算器
        """
        self._reset_calculator()
        self.expression_label.setText("")
        self._update_display()
    
    def _on_toggle_sign(self):
        """
        切换正负号
        """
        try:
            value = float(self._current_input)
            value = -value
            if value.is_integer():
                value = int(value)
            self._current_input = str(value)
            self._update_display()
        except ValueError:
            pass
    
    def _on_percent(self):
        """
        转换为百分比
        """
        try:
            value = float(self._current_input)
            value = value / 100
            self._current_input = str(value)
            self._update_display()
        except ValueError:
            pass
    
    def _on_show_history(self):
        """
        显示历史记录弹窗
        """
        dialog = HistoryDialog(self.widget() if hasattr(self, '_widget') else None, self._db)
        dialog.exec()
    
    def _save_to_history(self, operation, expression, result):
        """
        保存计算结果到历史记录
        """
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        history_id = self._db.insert('calculation_history', {
            'operation': operation,
            'expression': expression,
            'result': result,
            'created_at': now
        })
        
        return history_id > 0
    
    def _update_display(self):
        """
        更新显示
        """
        display_text = self._current_input
        
        try:
            value = float(display_text)
            if value.is_integer():
                display_text = str(int(value))
            else:
                if len(display_text) > 12:
                    display_text = f"{value:.6g}"
        except ValueError:
            pass
        
        self.display_label.setText(display_text)
    
    def widget(self):
        """
        获取当前widget引用
        """
        return getattr(self, '_widget', None)
