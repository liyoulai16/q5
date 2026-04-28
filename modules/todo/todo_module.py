#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
待办事项模块
用于任务管理的工具
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QListWidgetItem, QInputDialog, QMessageBox,
                             QLabel, QCheckBox, QComboBox, QDateEdit, QTextEdit,
                             QSplitter, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt, QDate, QDateTime
from PyQt6.QtGui import QFont

from modules.module_manager import BaseModule, ModuleCategory
from database.database_manager import DatabaseManager


class TodoModule(BaseModule):
    """
    待办事项模块
    提供任务创建、编辑、管理功能
    """
    
    PRIORITY_LOW = 0
    PRIORITY_MEDIUM = 1
    PRIORITY_HIGH = 2
    PRIORITY_URGENT = 3
    
    PRIORITY_NAMES = {
        PRIORITY_LOW: "低",
        PRIORITY_MEDIUM: "中",
        PRIORITY_HIGH: "高",
        PRIORITY_URGENT: "紧急"
    }
    
    STATUS_PENDING = 0
    STATUS_IN_PROGRESS = 1
    STATUS_COMPLETED = 2
    
    STATUS_NAMES = {
        STATUS_PENDING: "待处理",
        STATUS_IN_PROGRESS: "进行中",
        STATUS_COMPLETED: "已完成"
    }
    
    @property
    def module_id(self) -> str:
        return "todo"
    
    @property
    def name(self) -> str:
        return "待办事项"
    
    @property
    def description(self) -> str:
        return "任务管理工具，支持创建、编辑、跟踪任务进度"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def category(self) -> str:
        return ModuleCategory.DATA_MANAGEMENT
    
    @property
    def author(self) -> str:
        return "System"
    
    def _on_load(self) -> None:
        """
        模块加载时的初始化
        """
        self._db = DatabaseManager()
        self._create_todo_table()
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        pass
    
    def _create_todo_table(self):
        """
        创建待办事项数据表
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority INTEGER DEFAULT 1,
            status INTEGER DEFAULT 0,
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self._db.execute(create_table_sql)
        
        create_index_sql = "CREATE INDEX IF NOT EXISTS idx_todos_status ON todos(status)"
        self._db.execute(create_index_sql)
        
        create_index_sql = "CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority)"
        self._db.execute(create_index_sql)
    
    def _create_widget(self) -> QWidget:
        """
        创建待办事项的主界面
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)
        
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        todo_list_panel = self._create_todo_list_panel()
        content_splitter.addWidget(todo_list_panel)
        
        detail_panel = self._create_detail_panel()
        content_splitter.addWidget(detail_panel)
        
        content_splitter.setSizes([350, 650])
        
        main_layout.addWidget(content_splitter, 1)
        
        self._load_todo_list()
        
        return widget
    
    def _create_toolbar(self) -> QWidget:
        """
        创建工具栏
        """
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        new_btn = QPushButton("新建任务")
        new_btn.setStyleSheet("""
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
        new_btn.clicked.connect(self._on_new_todo)
        layout.addWidget(new_btn)
        
        delete_btn = QPushButton("删除任务")
        delete_btn.setStyleSheet("""
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
        delete_btn.clicked.connect(self._on_delete_todo)
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        filter_label = QLabel("筛选:")
        filter_label.setStyleSheet("font-weight: bold; color: #555;")
        layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "待处理", "进行中", "已完成"])
        self.filter_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.filter_combo)
        
        return toolbar
    
    def _create_todo_list_panel(self) -> QWidget:
        """
        创建待办事项列表面板
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        
        title_label = QLabel("任务列表")
        title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333; padding: 2px;")
        layout.addWidget(title_label)
        
        self.todo_list = QListWidget()
        self.todo_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 2px;
                padding: 0px;
            }
            QListWidget::item {
                padding: 4px;
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
        self.todo_list.currentRowChanged.connect(self._on_todo_selected)
        layout.addWidget(self.todo_list, 1)
        
        return panel
    
    def _create_detail_panel(self) -> QWidget:
        """
        创建详情面板
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        title_label = QLabel("任务详情")
        title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333; padding: 2px;")
        layout.addWidget(title_label)
        
        form_group = QGroupBox("基本信息")
        form_group.setStyleSheet("""
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
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(4)
        form_layout.setContentsMargins(8, 8, 8, 8)
        
        self.title_edit = QTextEdit()
        self.title_edit.setMaximumHeight(50)
        self.title_edit.setPlaceholderText("任务标题")
        self.title_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 2px;
                padding: 3px;
                background-color: #fafafa;
            }
        """)
        form_layout.addRow("标题:", self.title_edit)
        
        self.priority_combo = QComboBox()
        for priority_id, priority_name in self.PRIORITY_NAMES.items():
            self.priority_combo.addItem(priority_name, priority_id)
        self.priority_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border: 1px solid #ddd;
                border-radius: 2px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
        """)
        form_layout.addRow("优先级:", self.priority_combo)
        
        self.status_combo = QComboBox()
        for status_id, status_name in self.STATUS_NAMES.items():
            self.status_combo.addItem(status_name, status_id)
        self.status_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border: 1px solid #ddd;
                border-radius: 2px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
        """)
        form_layout.addRow("状态:", self.status_combo)
        
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(QDate.currentDate())
        self.due_date_edit.setSpecialValueText("无截止日期")
        self.due_date_edit.setStyleSheet("""
            QDateEdit {
                padding: 4px 8px;
                border: 1px solid #ddd;
                border-radius: 2px;
                background-color: white;
            }
            QDateEdit:hover {
                border-color: #2196F3;
            }
        """)
        form_layout.addRow("截止日期:", self.due_date_edit)
        
        layout.addWidget(form_group)
        
        desc_group = QGroupBox("任务描述")
        desc_group.setStyleSheet("""
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
        desc_layout = QVBoxLayout(desc_group)
        desc_layout.setContentsMargins(8, 8, 8, 8)
        desc_layout.setSpacing(0)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("输入任务详细描述...")
        self.description_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 2px;
                padding: 3px;
                background-color: #fafafa;
            }
        """)
        desc_layout.addWidget(self.description_edit)
        
        layout.addWidget(desc_group, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        btn_layout.setContentsMargins(0, 2, 0, 2)
        
        save_btn = QPushButton("保存修改")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 2px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        save_btn.clicked.connect(self._on_save_todo)
        btn_layout.addWidget(save_btn)
        
        complete_btn = QPushButton("标记完成")
        complete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                color: #333;
                border: none;
                padding: 6px 12px;
                border-radius: 2px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFB300;
            }
            QPushButton:pressed {
                background-color: #FFA000;
            }
        """)
        complete_btn.clicked.connect(self._on_mark_complete)
        btn_layout.addWidget(complete_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        self._clear_detail_panel()
        
        return panel
    
    def _load_todo_list(self, filter_status: int = None):
        """
        加载待办事项列表
        """
        self.todo_list.clear()
        
        if filter_status is None:
            todos = self._db.query_all("""
                SELECT id, title, priority, status, due_date 
                FROM todos 
                ORDER BY 
                    CASE status 
                        WHEN 0 THEN 0 
                        WHEN 1 THEN 1 
                        WHEN 2 THEN 2 
                    END,
                    priority DESC,
                    due_date ASC
            """)
        else:
            todos = self._db.query_all("""
                SELECT id, title, priority, status, due_date 
                FROM todos 
                WHERE status = ?
                ORDER BY priority DESC, due_date ASC
            """, (filter_status,))
        
        for todo in todos:
            status_text = self.STATUS_NAMES.get(todo['status'], "未知")
            priority_text = self.PRIORITY_NAMES.get(todo['priority'], "未知")
            
            display_text = f"[{status_text}] {todo['title']} (优先级: {priority_text})"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, todo['id'])
            
            if todo['status'] == self.STATUS_COMPLETED:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            elif todo['priority'] == self.PRIORITY_URGENT:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            self.todo_list.addItem(item)
    
    def _on_todo_selected(self, index):
        """
        当选择待办事项时触发
        """
        if index < 0:
            self._clear_detail_panel()
            return
        
        item = self.todo_list.item(index)
        todo_id = item.data(Qt.ItemDataRole.UserRole)
        
        todo = self._db.query_one(
            "SELECT * FROM todos WHERE id = ?",
            (todo_id,)
        )
        
        if todo:
            self._current_todo_id = todo_id
            self.title_edit.setPlainText(todo['title'])
            self.description_edit.setPlainText(todo['description'] if todo['description'] else "")
            
            priority_index = self.priority_combo.findData(todo['priority'])
            if priority_index >= 0:
                self.priority_combo.setCurrentIndex(priority_index)
            
            status_index = self.status_combo.findData(todo['status'])
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)
            
            if todo['due_date']:
                try:
                    date = QDate.fromString(todo['due_date'], "yyyy-MM-dd")
                    self.due_date_edit.setDate(date)
                except:
                    self.due_date_edit.setDate(QDate.currentDate())
            else:
                self.due_date_edit.setDate(self.due_date_edit.minimumDate())
    
    def _clear_detail_panel(self):
        """
        清空详情面板
        """
        self._current_todo_id = None
        self.title_edit.clear()
        self.description_edit.clear()
        self.priority_combo.setCurrentIndex(1)
        self.status_combo.setCurrentIndex(0)
        self.due_date_edit.setDate(QDate.currentDate())
    
    def _on_new_todo(self):
        """
        创建新任务
        """
        title, ok = QInputDialog.getText(
            None, "新建任务", "请输入任务标题:"
        )
        
        if ok and title.strip():
            now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            
            todo_id = self._db.insert('todos', {
                'title': title.strip(),
                'description': '',
                'priority': self.PRIORITY_MEDIUM,
                'status': self.STATUS_PENDING,
                'due_date': None,
                'created_at': now,
                'updated_at': now
            })
            
            if todo_id > 0:
                self._load_todo_list()
                
                for i in range(self.todo_list.count()):
                    item = self.todo_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == todo_id:
                        self.todo_list.setCurrentRow(i)
                        break
                
                QMessageBox.information(None, "成功", "任务创建成功！")
    
    def _on_save_todo(self):
        """
        保存任务
        """
        if not hasattr(self, '_current_todo_id') or self._current_todo_id is None:
            QMessageBox.warning(None, "警告", "请先选择或创建一个任务！")
            return
        
        title = self.title_edit.toPlainText().strip()
        if not title:
            QMessageBox.warning(None, "警告", "任务标题不能为空！")
            return
        
        description = self.description_edit.toPlainText()
        priority = self.priority_combo.currentData()
        status = self.status_combo.currentData()
        
        due_date = None
        if self.due_date_edit.date() != self.due_date_edit.minimumDate():
            due_date = self.due_date_edit.date().toString("yyyy-MM-dd")
        
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        affected = self._db.update(
            'todos',
            {
                'title': title,
                'description': description,
                'priority': priority,
                'status': status,
                'due_date': due_date,
                'updated_at': now
            },
            'id = ?',
            (self._current_todo_id,)
        )
        
        if affected > 0:
            current_filter = self.filter_combo.currentIndex()
            filter_status = None if current_filter == 0 else current_filter - 1
            self._load_todo_list(filter_status)
            
            QMessageBox.information(None, "成功", "任务保存成功！")
    
    def _on_delete_todo(self):
        """
        删除任务
        """
        current_row = self.todo_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(None, "警告", "请先选择要删除的任务！")
            return
        
        item = self.todo_list.item(current_row)
        todo_id = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            None, "确认删除",
            f"确定要删除任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            affected = self._db.delete('todos', 'id = ?', (todo_id,))
            
            if affected > 0:
                self._load_todo_list()
                self._clear_detail_panel()
                QMessageBox.information(None, "成功", "任务删除成功！")
    
    def _on_mark_complete(self):
        """
        标记任务为完成
        """
        if not hasattr(self, '_current_todo_id') or self._current_todo_id is None:
            QMessageBox.warning(None, "警告", "请先选择一个任务！")
            return
        
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        affected = self._db.update(
            'todos',
            {
                'status': self.STATUS_COMPLETED,
                'updated_at': now
            },
            'id = ?',
            (self._current_todo_id,)
        )
        
        if affected > 0:
            self.status_combo.setCurrentIndex(self.status_combo.findData(self.STATUS_COMPLETED))
            
            current_filter = self.filter_combo.currentIndex()
            filter_status = None if current_filter == 0 else current_filter - 1
            self._load_todo_list(filter_status)
            
            QMessageBox.information(None, "成功", "任务已标记为完成！")
    
    def _on_filter_changed(self, index):
        """
        筛选条件改变时触发
        """
        filter_status = None if index == 0 else index - 1
        self._load_todo_list(filter_status)
