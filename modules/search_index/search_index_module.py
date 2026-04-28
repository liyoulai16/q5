#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索索引模块
提供跨模块的数据搜索和索引管理功能
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QGroupBox, QFormLayout, QCheckBox, QComboBox,
                             QTabWidget, QTextEdit, QSplitter, QFrame,
                             QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QBrush

from modules.module_manager import BaseModule, ModuleCategory
from database.database_manager import DatabaseManager


class SearchIndexModule(BaseModule):
    """
    搜索索引模块
    提供跨模块的数据搜索和索引管理功能
    """
    
    @property
    def module_id(self) -> str:
        return "search_index"
    
    @property
    def name(self) -> str:
        return "搜索索引"
    
    @property
    def description(self) -> str:
        return "跨模块数据搜索工具，支持搜索笔记、待办事项、密码等数据"
    
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
        self._search_index: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._load_settings()
        self._build_search_index()
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        pass
    
    def _load_settings(self):
        """
        加载搜索设置
        """
        self._search_in_notes = self._db.get_setting(
            "search_in_notes", "true", self.module_id
        ).lower() == "true"
        self._search_in_todos = self._db.get_setting(
            "search_in_todos", "true", self.module_id
        ).lower() == "true"
        self._search_in_passwords = self._db.get_setting(
            "search_in_passwords", "true", self.module_id
        ).lower() == "true"
        self._search_in_pdf = self._db.get_setting(
            "search_in_pdf", "false", self.module_id
        ).lower() == "true"
        self._search_in_calculator = self._db.get_setting(
            "search_in_calculator", "false", self.module_id
        ).lower() == "true"
        self._search_case_sensitive = self._db.get_setting(
            "search_case_sensitive", "false", self.module_id
        ).lower() == "true"
        self._search_match_whole_word = self._db.get_setting(
            "search_match_whole_word", "false", self.module_id
        ).lower() == "true"
    
    def _save_settings(self):
        """
        保存搜索设置
        """
        self._db.set_setting("search_in_notes", str(self._search_in_notes).lower(), self.module_id)
        self._db.set_setting("search_in_todos", str(self._search_in_todos).lower(), self.module_id)
        self._db.set_setting("search_in_passwords", str(self._search_in_passwords).lower(), self.module_id)
        self._db.set_setting("search_in_pdf", str(self._search_in_pdf).lower(), self.module_id)
        self._db.set_setting("search_in_calculator", str(self._search_in_calculator).lower(), self.module_id)
        self._db.set_setting("search_case_sensitive", str(self._search_case_sensitive).lower(), self.module_id)
        self._db.set_setting("search_match_whole_word", str(self._search_match_whole_word).lower(), self.module_id)
    
    def _build_search_index(self):
        """
        构建搜索索引
        """
        self._search_index.clear()
        
        if self._search_in_notes:
            self._index_notes()
        
        if self._search_in_todos:
            self._index_todos()
        
        if self._search_in_passwords:
            self._index_passwords()
        
        if self._search_in_pdf:
            self._index_pdf_history()
        
        if self._search_in_calculator:
            self._index_calculator_history()
    
    def _index_notes(self):
        """
        索引笔记数据
        """
        try:
            notes = self._db.query_all(
                "SELECT id, title, content, created_at, updated_at FROM notes ORDER BY updated_at DESC"
            )
            
            for note in notes:
                self._search_index['notes'].append({
                    'id': note['id'],
                    'type': '笔记',
                    'type_icon': '📝',
                    'title': note['title'],
                    'content': note['content'] or '',
                    'created_at': note['created_at'],
                    'updated_at': note['updated_at'],
                    'search_text': f"{note['title']} {note['content'] or ''}",
                    'module': 'notepad'
                })
        except Exception as e:
            print(f"索引笔记失败: {e}")
    
    def _index_todos(self):
        """
        索引待办事项数据
        """
        try:
            todos = self._db.query_all("""
                SELECT id, title, description, priority, status, due_date, created_at, updated_at 
                FROM todos 
                ORDER BY created_at DESC
            """)
            
            priority_names = {0: "低", 1: "中", 2: "高", 3: "紧急"}
            status_names = {0: "待处理", 1: "进行中", 2: "已完成"}
            
            for todo in todos:
                priority_name = priority_names.get(todo['priority'], "未知")
                status_name = status_names.get(todo['status'], "未知")
                
                self._search_index['todos'].append({
                    'id': todo['id'],
                    'type': '待办事项',
                    'type_icon': '📋',
                    'title': todo['title'],
                    'content': todo['description'] or '',
                    'priority': priority_name,
                    'status': status_name,
                    'due_date': todo['due_date'],
                    'created_at': todo['created_at'],
                    'updated_at': todo['updated_at'],
                    'search_text': f"{todo['title']} {todo['description'] or ''} {priority_name} {status_name}",
                    'module': 'todo'
                })
        except Exception as e:
            print(f"索引待办事项失败: {e}")
    
    def _index_passwords(self):
        """
        索引密码管理器数据
        """
        try:
            passwords = self._db.query_all("""
                SELECT id, title, username, website, category, notes, created_at, updated_at 
                FROM passwords 
                ORDER BY updated_at DESC
            """)
            
            for pwd in passwords:
                self._search_index['passwords'].append({
                    'id': pwd['id'],
                    'type': '密码',
                    'type_icon': '🔐',
                    'title': pwd['title'],
                    'content': f"{pwd['username'] or ''} {pwd['website'] or ''} {pwd['notes'] or ''}",
                    'username': pwd['username'],
                    'website': pwd['website'],
                    'category': pwd['category'],
                    'created_at': pwd['created_at'],
                    'updated_at': pwd['updated_at'],
                    'search_text': f"{pwd['title']} {pwd['username'] or ''} {pwd['website'] or ''} {pwd['notes'] or ''} {pwd['category']}",
                    'module': 'password_manager'
                })
        except Exception as e:
            print(f"索引密码失败: {e}")
    
    def _index_pdf_history(self):
        """
        索引PDF操作历史
        """
        try:
            pdf_ops = self._db.query_all("""
                SELECT id, operation, source_file, target_file, details, created_at 
                FROM pdf_operations 
                ORDER BY created_at DESC
            """)
            
            for op in pdf_ops:
                self._search_index['pdf'].append({
                    'id': op['id'],
                    'type': 'PDF操作',
                    'type_icon': '📄',
                    'title': op['operation'],
                    'content': f"{op['source_file'] or ''} {op['target_file'] or ''} {op['details'] or ''}",
                    'operation': op['operation'],
                    'source_file': op['source_file'],
                    'target_file': op['target_file'],
                    'details': op['details'],
                    'created_at': op['created_at'],
                    'search_text': f"{op['operation']} {op['source_file'] or ''} {op['target_file'] or ''} {op['details'] or ''}",
                    'module': 'pdf_tool'
                })
        except Exception as e:
            print(f"索引PDF历史失败: {e}")
    
    def _index_calculator_history(self):
        """
        索引计算器历史
        """
        try:
            calc_history = self._db.query_all("""
                SELECT id, operation, expression, result, created_at 
                FROM calculation_history 
                ORDER BY created_at DESC
            """)
            
            for calc in calc_history:
                self._search_index['calculator'].append({
                    'id': calc['id'],
                    'type': '计算记录',
                    'type_icon': '🔢',
                    'title': f"{calc['expression']} = {calc['result']}",
                    'content': f"{calc['operation'] or ''}",
                    'operation': calc['operation'],
                    'expression': calc['expression'],
                    'result': calc['result'],
                    'created_at': calc['created_at'],
                    'search_text': f"{calc['expression']} {calc['result']} {calc['operation'] or ''}",
                    'module': 'table_calculator'
                })
        except Exception as e:
            print(f"索引计算器历史失败: {e}")
    
    def _search(self, query: str) -> List[Dict[str, Any]]:
        """
        执行搜索
        返回匹配的结果列表
        """
        if not query.strip():
            return []
        
        results = []
        
        flags = 0 if self._search_case_sensitive else re.IGNORECASE
        
        if self._search_match_whole_word:
            pattern = r'\b' + re.escape(query) + r'\b'
        else:
            pattern = re.escape(query)
        
        regex = re.compile(pattern, flags)
        
        for category, items in self._search_index.items():
            for item in items:
                if regex.search(item['search_text']):
                    score = self._calculate_relevance(item, query)
                    results.append({
                        **item,
                        'relevance': score,
                        'match_text': self._highlight_match(item['search_text'], query)
                    })
        
        results.sort(key=lambda x: x['relevance'], reverse=True)
        
        return results
    
    def _calculate_relevance(self, item: Dict[str, Any], query: str) -> int:
        """
        计算搜索结果的相关性分数
        """
        score = 0
        query_lower = query.lower()
        title_lower = item['title'].lower()
        content_lower = item['content'].lower()
        
        if title_lower == query_lower:
            score += 100
        elif query_lower in title_lower:
            score += 50
        
        if query_lower in content_lower:
            score += 20
        
        if 'updated_at' in item and item['updated_at']:
            try:
                update_date = datetime.strptime(item['updated_at'], "%Y-%m-%d %H:%M:%S")
                days_ago = (datetime.now() - update_date).days
                if days_ago < 7:
                    score += 10
                elif days_ago < 30:
                    score += 5
            except:
                pass
        
        return score
    
    def _highlight_match(self, text: str, query: str) -> str:
        """
        高亮匹配的文本
        """
        if not query:
            return text
        
        flags = 0 if self._search_case_sensitive else re.IGNORECASE
        pattern = re.compile(re.escape(query), flags)
        
        def replace_func(match):
            return f"【{match.group()}】"
        
        return pattern.sub(replace_func, text[:200] + ("..." if len(text) > 200 else ""))
    
    def _get_index_stats(self) -> Dict[str, int]:
        """
        获取索引统计信息
        """
        stats = {}
        for category, items in self._search_index.items():
            stats[category] = len(items)
        return stats
    
    def _create_widget(self) -> QWidget:
        """
        创建搜索索引模块的主界面
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)
        
        self._tab_widget = QTabWidget()
        self._tab_widget.setFont(QFont("Microsoft YaHei", 10))
        self._tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)
        
        search_tab = self._create_search_tab()
        index_tab = self._create_index_tab()
        settings_tab = self._create_settings_tab()
        
        self._tab_widget.addTab(search_tab, "🔍 搜索")
        self._tab_widget.addTab(index_tab, "📊 索引管理")
        self._tab_widget.addTab(settings_tab, "⚙️ 设置")
        
        main_layout.addWidget(self._tab_widget, 1)
        
        return widget
    
    def _create_search_tab(self) -> QWidget:
        """
        创建搜索选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("数据搜索")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        layout.addWidget(title_label)
        
        search_group = QGroupBox("搜索条件")
        search_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        search_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
        """)
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(10)
        
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        
        search_label = QLabel("搜索关键词:")
        search_label.setFont(QFont("Microsoft YaHei", 10))
        input_row.addWidget(search_label)
        
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("输入搜索关键词...")
        self._search_input.setFont(QFont("Microsoft YaHei", 11))
        self._search_input.setMinimumHeight(40)
        self._search_input.setStyleSheet("""
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
        self._search_input.returnPressed.connect(self._on_search)
        input_row.addWidget(self._search_input, 1)
        
        self._search_btn = QPushButton("🔍 搜索")
        self._search_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._search_btn.setMinimumHeight(40)
        self._search_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 25px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self._search_btn.clicked.connect(self._on_search)
        input_row.addWidget(self._search_btn)
        
        search_layout.addLayout(input_row)
        
        quick_filters_row = QHBoxLayout()
        quick_filters_row.setSpacing(10)
        
        filter_label = QLabel("快速筛选:")
        filter_label.setFont(QFont("Microsoft YaHei", 10))
        quick_filters_row.addWidget(filter_label)
        
        self._quick_filters = {
            'all': QPushButton("📁 全部"),
            'notes': QPushButton("📝 笔记"),
            'todos': QPushButton("📋 待办"),
            'passwords': QPushButton("🔐 密码"),
        }
        
        for key, btn in self._quick_filters.items():
            btn.setFont(QFont("Microsoft YaHei", 9))
            btn.setMinimumHeight(30)
            btn.setCheckable(True)
            btn.setChecked(key == 'all')
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            if key == 'all':
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1565C0;
                        color: white;
                        border: none;
                        border-radius: 15px;
                        padding: 5px 15px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f5f5f5;
                        color: #666;
                        border: 1px solid #ddd;
                        border-radius: 15px;
                        padding: 5px 15px;
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
            
            btn.clicked.connect(lambda checked, k=key: self._on_quick_filter_changed(k))
            quick_filters_row.addWidget(btn)
        
        quick_filters_row.addStretch()
        
        search_layout.addLayout(quick_filters_row)
        
        layout.addWidget(search_group)
        
        results_group = QGroupBox("搜索结果")
        results_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        results_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
        """)
        results_layout = QVBoxLayout(results_group)
        results_layout.setSpacing(10)
        
        self._results_label = QLabel("输入关键词并点击搜索...")
        self._results_label.setFont(QFont("Microsoft YaHei", 10))
        self._results_label.setStyleSheet("color: #666;")
        results_layout.addWidget(self._results_label)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(5)
        
        self._results_list = QListWidget()
        self._results_list.setFont(QFont("Microsoft YaHei", 10))
        self._results_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
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
        self._results_list.currentRowChanged.connect(self._on_result_selected)
        list_layout.addWidget(self._results_list, 1)
        
        splitter.addWidget(list_panel)
        
        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(5)
        
        detail_title = QLabel("结果详情")
        detail_title.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        detail_title.setStyleSheet("color: #333;")
        detail_layout.addWidget(detail_title)
        
        self._result_detail_text = QTextEdit()
        self._result_detail_text.setFont(QFont("Microsoft YaHei", 10))
        self._result_detail_text.setReadOnly(True)
        self._result_detail_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                background-color: #fafafa;
            }
        """)
        detail_layout.addWidget(self._result_detail_text, 1)
        
        splitter.addWidget(detail_panel)
        splitter.setSizes([350, 450])
        
        results_layout.addWidget(splitter, 1)
        
        layout.addWidget(results_group, 1)
        
        return tab
    
    def _create_index_tab(self) -> QWidget:
        """
        创建索引管理选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        title_label = QLabel("索引管理")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        layout.addWidget(title_label)
        
        stats_group = QGroupBox("索引统计")
        stats_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        stats_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
        """)
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(10)
        
        self._stats_text = QLabel("")
        self._stats_text.setFont(QFont("Microsoft YaHei", 10))
        self._stats_text.setStyleSheet("color: #333; line-height: 1.8;")
        stats_layout.addWidget(self._stats_text)
        
        layout.addWidget(stats_group)
        
        actions_group = QGroupBox("索引操作")
        actions_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        actions_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
        """)
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setSpacing(15)
        
        self._rebuild_index_btn = QPushButton("🔄 重建索引")
        self._rebuild_index_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._rebuild_index_btn.setMinimumHeight(45)
        self._rebuild_index_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self._rebuild_index_btn.clicked.connect(self._on_rebuild_index)
        actions_layout.addWidget(self._rebuild_index_btn)
        
        self._refresh_stats_btn = QPushButton("📊 刷新统计")
        self._refresh_stats_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._refresh_stats_btn.setMinimumHeight(45)
        self._refresh_stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        self._refresh_stats_btn.clicked.connect(self._update_stats_display)
        actions_layout.addWidget(self._refresh_stats_btn)
        
        actions_layout.addStretch()
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
        
        self._update_stats_display()
        
        return tab
    
    def _create_settings_tab(self) -> QWidget:
        """
        创建设置选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        title_label = QLabel("搜索设置")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        layout.addWidget(title_label)
        
        settings_group = QGroupBox("搜索范围设置")
        settings_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        settings_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
        """)
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)
        
        self._scope_checkboxes = {
            'notes': QCheckBox("📝 搜索笔记内容"),
            'todos': QCheckBox("📋 搜索待办事项"),
            'passwords': QCheckBox("🔐 搜索密码记录"),
            'pdf': QCheckBox("📄 搜索PDF操作历史"),
            'calculator': QCheckBox("🔢 搜索计算历史"),
        }
        
        for key, cb in self._scope_checkboxes.items():
            cb.setFont(QFont("Microsoft YaHei", 10))
            cb.setChecked(getattr(self, f"_search_in_{key}", False))
            cb.setStyleSheet("""
                QCheckBox {
                    spacing: 10px;
                    padding: 5px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)
            settings_layout.addWidget(cb)
        
        layout.addWidget(settings_group)
        
        options_group = QGroupBox("搜索选项")
        options_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        options_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
        """)
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(10)
        
        self._case_sensitive_cb = QCheckBox("区分大小写")
        self._case_sensitive_cb.setFont(QFont("Microsoft YaHei", 10))
        self._case_sensitive_cb.setChecked(self._search_case_sensitive)
        self._case_sensitive_cb.setStyleSheet("""
            QCheckBox {
                spacing: 10px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        options_layout.addWidget(self._case_sensitive_cb)
        
        self._match_whole_word_cb = QCheckBox("匹配完整单词")
        self._match_whole_word_cb.setFont(QFont("Microsoft YaHei", 10))
        self._match_whole_word_cb.setChecked(self._search_match_whole_word)
        self._match_whole_word_cb.setStyleSheet("""
            QCheckBox {
                spacing: 10px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        options_layout.addWidget(self._match_whole_word_cb)
        
        layout.addWidget(options_group)
        
        save_row = QHBoxLayout()
        
        self._save_settings_btn = QPushButton("💾 保存设置")
        self._save_settings_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._save_settings_btn.setMinimumHeight(45)
        self._save_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self._save_settings_btn.clicked.connect(self._on_save_search_settings)
        save_row.addWidget(self._save_settings_btn)
        
        save_row.addStretch()
        
        layout.addLayout(save_row)
        
        layout.addStretch()
        
        return tab
    
    def _on_search(self):
        """
        执行搜索按钮点击
        """
        query = self._search_input.text().strip()
        
        if not query:
            QMessageBox.warning(None, "提示", "请输入搜索关键词！")
            return
        
        self._results_label.setText("正在搜索...")
        self._results_list.clear()
        self._result_detail_text.clear()
        
        results = self._search(query)
        
        if self._current_filter != 'all':
            results = [r for r in results if r['module'].replace('_', '') == self._current_filter or 
                       r.get('type', '').lower().startswith(self._current_filter.rstrip('s'))]
        
        if not results:
            self._results_label.setText(f"未找到与 \"{query}\" 相关的结果")
            item = QListWidgetItem("无匹配结果")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._results_list.addItem(item)
            return
        
        self._results_label.setText(f"找到 {len(results)} 个相关结果")
        
        for result in results:
            display_text = f"{result['type_icon']} {result['type']}\n"
            display_text += f"   标题: {result['title']}\n"
            if result.get('updated_at'):
                display_text += f"   更新时间: {result['updated_at']}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, result)
            
            if result['relevance'] >= 50:
                item.setForeground(QBrush(QColor("#1565C0")))
            
            self._results_list.addItem(item)
    
    def _on_quick_filter_changed(self, key: str):
        """
        快速筛选器改变
        """
        for k, btn in self._quick_filters.items():
            if k == key:
                btn.setChecked(True)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1565C0;
                        color: white;
                        border: none;
                        border-radius: 15px;
                        padding: 5px 15px;
                    }
                """)
            else:
                btn.setChecked(False)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f5f5f5;
                        color: #666;
                        border: 1px solid #ddd;
                        border-radius: 15px;
                        padding: 5px 15px;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                """)
        
        self._current_filter = key
        
        if self._search_input.text().strip():
            self._on_search()
    
    def _on_result_selected(self, index):
        """
        搜索结果选中
        """
        if index < 0:
            self._result_detail_text.clear()
            return
        
        item = self._results_list.item(index)
        if not item:
            return
        
        result = item.data(Qt.ItemDataRole.UserRole)
        if not result:
            return
        
        detail_text = f"""
<b>类型:</b> {result['type_icon']} {result['type']}

<b>标题:</b> {result['title']}

<b>内容预览:</b> {result.get('match_text', result.get('content', '')[:200])}

<b>相关度:</b> {result['relevance']} 分
"""
        
        if result.get('created_at'):
            detail_text += f"\n<b>创建时间:</b> {result['created_at']}"
        
        if result.get('updated_at'):
            detail_text += f"\n<b>更新时间:</b> {result['updated_at']}"
        
        if result.get('status'):
            detail_text += f"\n<b>状态:</b> {result['status']}"
        
        if result.get('priority'):
            detail_text += f"\n<b>优先级:</b> {result['priority']}"
        
        if result.get('website'):
            detail_text += f"\n<b>网站:</b> {result['website']}"
        
        if result.get('username'):
            detail_text += f"\n<b>用户名:</b> {result['username']}"
        
        self._result_detail_text.setHtml(detail_text.replace('\n', '<br>'))
    
    def _on_rebuild_index(self):
        """
        重建索引按钮点击
        """
        reply = QMessageBox.question(
            None, "确认重建",
            "确定要重建搜索索引吗？\n"
            "这将重新扫描所有数据并构建索引。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._build_search_index()
            self._update_stats_display()
            QMessageBox.information(None, "成功", "搜索索引已重建！")
    
    def _update_stats_display(self):
        """
        更新统计显示
        """
        stats = self._get_index_stats()
        total = sum(stats.values())
        
        category_names = {
            'notes': '笔记',
            'todos': '待办事项',
            'passwords': '密码记录',
            'pdf': 'PDF操作历史',
            'calculator': '计算历史'
        }
        
        stats_text = f"<b>索引总记录数:</b> {total}<br><br>"
        stats_text += "<b>各分类统计:</b><br>"
        
        for key, count in stats.items():
            name = category_names.get(key, key)
            stats_text += f"  • {name}: {count} 条<br>"
        
        self._stats_text.setText(stats_text)
    
    def _on_save_search_settings(self):
        """
        保存搜索设置
        """
        for key, cb in self._scope_checkboxes.items():
            setattr(self, f"_search_in_{key}", cb.isChecked())
        
        self._search_case_sensitive = self._case_sensitive_cb.isChecked()
        self._search_match_whole_word = self._match_whole_word_cb.isChecked()
        
        self._save_settings()
        
        self._build_search_index()
        self._update_stats_display()
        
        QMessageBox.information(None, "成功", "设置已保存，索引已更新！")
    
    def showEvent(self, event):
        """
        显示事件
        """
        super().showEvent(event)
        if hasattr(self, '_current_filter'):
            pass
        else:
            self._current_filter = 'all'
