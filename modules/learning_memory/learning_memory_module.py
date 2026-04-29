#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习与记忆模块
提供学习计划制定、复习提醒和学习进度追踪功能
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QListWidgetItem, QInputDialog, QMessageBox,
                             QLabel, QComboBox, QDateEdit, QTextEdit, QSplitter,
                             QGroupBox, QFormLayout, QTabWidget, QSpinBox, 
                             QTimeEdit, QCheckBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QProgressBar, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QDate, QDateTime, QTimer, QSize
from PyQt6.QtGui import QFont, QColor

from modules.module_manager import BaseModule, ModuleCategory
from database.database_manager import DatabaseManager


class LearningMemoryModule(BaseModule):
    """
    学习与记忆模块
    提供学习计划制定、复习提醒和学习进度追踪功能
    """
    
    # 计划状态
    PLAN_STATUS_NOT_STARTED = 0
    PLAN_STATUS_IN_PROGRESS = 1
    PLAN_STATUS_COMPLETED = 2
    PLAN_STATUS_PAUSED = 3
    
    PLAN_STATUS_NAMES = {
        PLAN_STATUS_NOT_STARTED: "未开始",
        PLAN_STATUS_IN_PROGRESS: "进行中",
        PLAN_STATUS_COMPLETED: "已完成",
        PLAN_STATUS_PAUSED: "已暂停"
    }
    
    # 任务状态
    TASK_STATUS_NOT_STARTED = 0
    TASK_STATUS_IN_PROGRESS = 1
    TASK_STATUS_COMPLETED = 2
    
    TASK_STATUS_NAMES = {
        TASK_STATUS_NOT_STARTED: "未开始",
        TASK_STATUS_IN_PROGRESS: "进行中",
        TASK_STATUS_COMPLETED: "已完成"
    }
    
    # 提醒方式
    REMINDER_METHOD_SYSTEM = 0
    REMINDER_METHOD_SOUND = 1
    REMINDER_METHOD_BOTH = 2
    
    REMINDER_METHOD_NAMES = {
        REMINDER_METHOD_SYSTEM: "系统通知",
        REMINDER_METHOD_SOUND: "声音提醒",
        REMINDER_METHOD_BOTH: "系统+声音"
    }
    
    # 优先级
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
    
    @property
    def module_id(self) -> str:
        return "learning_memory"
    
    @property
    def name(self) -> str:
        return "学习与记忆"
    
    @property
    def description(self) -> str:
        return "学习计划制定、复习提醒和学习进度追踪工具，帮助高效学习和记忆"
    
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
        self._create_tables()
        self._reminder_timer = None
        self._start_reminder_check()
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        if self._reminder_timer:
            self._reminder_timer.stop()
    
    def _create_tables(self):
        """
        创建所有数据表
        """
        # 学习计划表
        create_plans_table = """
        CREATE TABLE IF NOT EXISTS study_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            start_date DATE,
            end_date DATE,
            total_hours REAL DEFAULT 0,
            completed_hours REAL DEFAULT 0,
            status INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self._db.execute(create_plans_table)
        
        # 学习任务表
        create_tasks_table = """
        CREATE TABLE IF NOT EXISTS study_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            priority INTEGER DEFAULT 1,
            scheduled_date DATE,
            estimated_hours REAL DEFAULT 1,
            actual_hours REAL DEFAULT 0,
            status INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES study_plans(id)
        )
        """
        self._db.execute(create_tasks_table)
        
        # 复习提醒表
        create_reminders_table = """
        CREATE TABLE IF NOT EXISTS review_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            reminder_time TIMESTAMP NOT NULL,
            reminder_method INTEGER DEFAULT 0,
            is_enabled INTEGER DEFAULT 1,
            is_sent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES study_tasks(id)
        )
        """
        self._db.execute(create_reminders_table)
        
        # 学习进度记录表
        create_progress_table = """
        CREATE TABLE IF NOT EXISTS study_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER,
            task_id INTEGER,
            study_date DATE NOT NULL,
            hours_studied REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES study_plans(id),
            FOREIGN KEY (task_id) REFERENCES study_tasks(id)
        )
        """
        self._db.execute(create_progress_table)
        
        # 创建索引
        self._db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_plan ON study_tasks(plan_id)")
        self._db.execute("CREATE INDEX IF NOT EXISTS idx_reminders_task ON review_reminders(task_id)")
        self._db.execute("CREATE INDEX IF NOT EXISTS idx_progress_plan ON study_progress(plan_id)")
        self._db.execute("CREATE INDEX IF NOT EXISTS idx_progress_date ON study_progress(study_date)")
    
    def _start_reminder_check(self):
        """
        启动提醒检查定时器
        """
        self._reminder_timer = QTimer()
        self._reminder_timer.timeout.connect(self._check_reminders)
        self._reminder_timer.start(60000)  # 每分钟检查一次
    
    def _check_reminders(self):
        """
        检查是否有需要触发的提醒
        """
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        pending_reminders = self._db.query_all("""
            SELECT r.*, t.title as task_title
            FROM review_reminders r
            JOIN study_tasks t ON r.task_id = t.id
            WHERE r.is_enabled = 1 AND r.is_sent = 0 AND r.reminder_time <= ?
        """, (now,))
        
        for reminder in pending_reminders:
            self._show_reminder(reminder)
            self._db.update(
                'review_reminders',
                {'is_sent': 1},
                'id = ?',
                (reminder['id'],)
            )
    
    def _show_reminder(self, reminder):
        """
        显示提醒
        """
        method = reminder['reminder_method']
        title = reminder['task_title']
        reminder_time = reminder['reminder_time']
        
        message = f"复习提醒：\n任务：{title}\n提醒时间：{reminder_time}"
        
        # 系统通知方式
        if method in [self.REMINDER_METHOD_SYSTEM, self.REMINDER_METHOD_BOTH]:
            QMessageBox.information(None, "复习提醒", message)
        
        # 声音提醒方式（这里简化处理，实际可以实现播放声音）
        if method in [self.REMINDER_METHOD_SOUND, self.REMINDER_METHOD_BOTH]:
            print(f"[声音提醒] {message}")
    
    def _create_widget(self) -> QWidget:
        """
        创建学习与记忆模块的主界面
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建标签页
        self._tab_widget = QTabWidget()
        self._tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
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
                border-bottom: 1px solid white;
                font-weight: bold;
                color: #2196F3;
            }
            QTabBar::tab:hover {
                background-color: #e3f2fd;
            }
        """)
        
        # 添加三个标签页
        self._tab_widget.addTab(self._create_study_plans_tab(), "📚 学习计划")
        self._tab_widget.addTab(self._create_review_reminders_tab(), "🔔 复习提醒")
        self._tab_widget.addTab(self._create_progress_tracking_tab(), "📊 进度追踪")
        
        main_layout.addWidget(self._tab_widget)
        
        return widget
    
    def _create_study_plans_tab(self) -> QWidget:
        """
        创建学习计划标签页
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 工具栏
        toolbar = self._create_plans_toolbar()
        layout.addWidget(toolbar)
        
        # 内容区域：左侧计划列表，右侧计划详情和任务列表
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        # 左侧：计划列表
        plans_panel = self._create_plans_list_panel()
        content_splitter.addWidget(plans_panel)
        
        # 右侧：计划详情和任务列表
        right_panel = self._create_plan_detail_panel()
        content_splitter.addWidget(right_panel)
        
        content_splitter.setSizes([300, 700])
        
        layout.addWidget(content_splitter, 1)
        
        # 加载计划列表
        self._load_study_plans()
        
        return widget
    
    def _create_plans_toolbar(self) -> QWidget:
        """
        创建学习计划工具栏
        """
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 新建计划按钮
        new_plan_btn = QPushButton("新建计划")
        new_plan_btn.setStyleSheet("""
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
        new_plan_btn.clicked.connect(self._on_new_study_plan)
        layout.addWidget(new_plan_btn)
        
        # 新建任务按钮
        new_task_btn = QPushButton("新建任务")
        new_task_btn.setStyleSheet("""
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
        new_task_btn.clicked.connect(self._on_new_task)
        layout.addWidget(new_task_btn)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
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
        delete_btn.clicked.connect(self._on_delete_plan)
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        # 筛选标签
        filter_label = QLabel("状态筛选:")
        filter_label.setStyleSheet("font-weight: bold; color: #555;")
        layout.addWidget(filter_label)
        
        self._plan_filter_combo = QComboBox()
        self._plan_filter_combo.addItems(["全部", "未开始", "进行中", "已完成", "已暂停"])
        self._plan_filter_combo.setStyleSheet("""
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
        """)
        self._plan_filter_combo.currentIndexChanged.connect(self._on_plan_filter_changed)
        layout.addWidget(self._plan_filter_combo)
        
        return toolbar
    
    def _create_plans_list_panel(self) -> QWidget:
        """
        创建学习计划列表面板
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 标题
        title_label = QLabel("学习计划列表")
        title_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333;")
        layout.addWidget(title_label)
        
        # 计划列表
        self._plans_list = QListWidget()
        self._plans_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background-color: #fafafa;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565C0;
                border: 1px solid #2196F3;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self._plans_list.currentRowChanged.connect(self._on_plan_selected)
        layout.addWidget(self._plans_list, 1)
        
        return panel
    
    def _create_plan_detail_panel(self) -> QWidget:
        """
        创建计划详情面板
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 计划详情分组
        detail_group = QGroupBox("计划详情")
        detail_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
                color: #333;
            }
        """)
        
        detail_layout = QFormLayout(detail_group)
        detail_layout.setSpacing(8)
        detail_layout.setContentsMargins(15, 15, 15, 15)
        
        # 计划标题
        self._plan_title_edit = QTextEdit()
        self._plan_title_edit.setMaximumHeight(50)
        self._plan_title_edit.setPlaceholderText("计划标题")
        self._plan_title_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background-color: #fafafa;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #2196F3;
            }
        """)
        detail_layout.addRow("计划标题:", self._plan_title_edit)
        
        # 日期行
        date_layout = QHBoxLayout()
        
        start_label = QLabel("开始日期:")
        start_label.setStyleSheet("font-weight: normal;")
        date_layout.addWidget(start_label)
        
        self._plan_start_date = QDateEdit()
        self._plan_start_date.setCalendarPopup(True)
        self._plan_start_date.setDate(QDate.currentDate())
        self._plan_start_date.setStyleSheet("""
            QDateEdit {
                padding: 5px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QDateEdit:hover {
                border-color: #2196F3;
            }
        """)
        date_layout.addWidget(self._plan_start_date)
        
        end_label = QLabel("结束日期:")
        end_label.setStyleSheet("font-weight: normal; margin-left: 20px;")
        date_layout.addWidget(end_label)
        
        self._plan_end_date = QDateEdit()
        self._plan_end_date.setCalendarPopup(True)
        self._plan_end_date.setDate(QDate.currentDate().addDays(30))
        self._plan_end_date.setStyleSheet("""
            QDateEdit {
                padding: 5px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QDateEdit:hover {
                border-color: #2196F3;
            }
        """)
        date_layout.addWidget(self._plan_end_date)
        
        date_layout.addStretch()
        detail_layout.addRow(date_layout)
        
        # 学时行
        hours_layout = QHBoxLayout()
        
        total_label = QLabel("总学时:")
        total_label.setStyleSheet("font-weight: normal;")
        hours_layout.addWidget(total_label)
        
        self._plan_total_hours = QSpinBox()
        self._plan_total_hours.setRange(1, 10000)
        self._plan_total_hours.setValue(100)
        self._plan_total_hours.setSuffix(" 小时")
        self._plan_total_hours.setStyleSheet("""
            QSpinBox {
                padding: 5px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QSpinBox:hover {
                border-color: #2196F3;
            }
        """)
        hours_layout.addWidget(self._plan_total_hours)
        
        hours_layout.addStretch()
        detail_layout.addRow(hours_layout)
        
        # 状态
        status_layout = QHBoxLayout()
        status_label = QLabel("状态:")
        status_label.setStyleSheet("font-weight: normal;")
        status_layout.addWidget(status_label)
        
        self._plan_status_combo = QComboBox()
        for status_id, status_name in self.PLAN_STATUS_NAMES.items():
            self._plan_status_combo.addItem(status_name, status_id)
        self._plan_status_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
        """)
        status_layout.addWidget(self._plan_status_combo)
        status_layout.addStretch()
        detail_layout.addRow(status_layout)
        
        # 描述
        desc_label = QLabel("计划描述:")
        desc_label.setStyleSheet("font-weight: normal;")
        detail_layout.addRow(desc_label)
        
        self._plan_description_edit = QTextEdit()
        self._plan_description_edit.setPlaceholderText("输入计划详细描述...")
        self._plan_description_edit.setMinimumHeight(80)
        self._plan_description_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background-color: #fafafa;
            }
            QTextEdit:focus {
                border-color: #2196F3;
            }
        """)
        detail_layout.addRow(self._plan_description_edit)
        
        # 保存按钮
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        save_plan_btn = QPushButton("保存计划")
        save_plan_btn.setMinimumWidth(120)
        save_plan_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 20px;
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
        save_plan_btn.clicked.connect(self._on_save_plan)
        save_layout.addWidget(save_plan_btn)
        
        detail_layout.addRow(save_layout)
        
        layout.addWidget(detail_group)
        
        # 任务列表分组
        tasks_group = QGroupBox("计划任务")
        tasks_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
                color: #333;
            }
        """)
        
        tasks_layout = QVBoxLayout(tasks_group)
        tasks_layout.setContentsMargins(10, 10, 10, 10)
        tasks_layout.setSpacing(5)
        
        # 任务表格
        self._tasks_table = QTableWidget()
        self._tasks_table.setColumnCount(6)
        self._tasks_table.setHorizontalHeaderLabels(["任务标题", "优先级", "计划日期", "预估学时", "实际学时", "状态"])
        self._tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tasks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tasks_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._tasks_table.setAlternatingRowColors(True)
        self._tasks_table.setStyleSheet("""
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
                border: none;
                border-bottom: 2px solid #ddd;
                font-weight: bold;
            }
        """)
        self._tasks_table.itemDoubleClicked.connect(self._on_task_double_clicked)
        tasks_layout.addWidget(self._tasks_table)
        
        layout.addWidget(tasks_group, 1)
        
        # 初始化详情面板
        self._clear_plan_detail_panel()
        
        return panel
    
    def _create_review_reminders_tab(self) -> QWidget:
        """
        创建复习提醒标签页
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 工具栏
        toolbar = self._create_reminders_toolbar()
        layout.addWidget(toolbar)
        
        # 内容区域：左侧任务列表，右侧提醒设置
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        # 左侧：待复习任务列表
        tasks_panel = self._create_review_tasks_panel()
        content_splitter.addWidget(tasks_panel)
        
        # 右侧：提醒设置
        reminder_panel = self._create_reminder_settings_panel()
        content_splitter.addWidget(reminder_panel)
        
        content_splitter.setSizes([400, 600])
        
        layout.addWidget(content_splitter, 1)
        
        # 加载待复习任务
        self._load_review_tasks()
        
        return widget
    
    def _create_reminders_toolbar(self) -> QWidget:
        """
        创建复习提醒工具栏
        """
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 新建提醒按钮
        new_reminder_btn = QPushButton("新建提醒")
        new_reminder_btn.setStyleSheet("""
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
        new_reminder_btn.clicked.connect(self._on_new_reminder)
        layout.addWidget(new_reminder_btn)
        
        # 删除提醒按钮
        delete_reminder_btn = QPushButton("删除提醒")
        delete_reminder_btn.setStyleSheet("""
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
        delete_reminder_btn.clicked.connect(self._on_delete_reminder)
        layout.addWidget(delete_reminder_btn)
        
        layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("""
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
        refresh_btn.clicked.connect(self._load_review_tasks)
        layout.addWidget(refresh_btn)
        
        return toolbar
    
    def _create_review_tasks_panel(self) -> QWidget:
        """
        创建待复习任务列表面板
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 标题
        title_label = QLabel("待复习任务列表")
        title_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333;")
        layout.addWidget(title_label)
        
        # 任务列表
        self._review_tasks_list = QListWidget()
        self._review_tasks_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background-color: #fafafa;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #fff3e0;
                color: #E65100;
                border: 1px solid #FF9800;
            }
            QListWidget::item:hover {
                background-color: #fff8e1;
            }
        """)
        self._review_tasks_list.currentRowChanged.connect(self._on_review_task_selected)
        layout.addWidget(self._review_tasks_list, 1)
        
        return panel
    
    def _create_reminder_settings_panel(self) -> QWidget:
        """
        创建提醒设置面板
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 提醒设置分组
        settings_group = QGroupBox("提醒设置")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
                color: #333;
            }
        """)
        
        settings_layout = QFormLayout(settings_group)
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(15, 15, 15, 15)
        
        # 任务信息
        self._reminder_task_label = QLabel("未选择任务")
        self._reminder_task_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        settings_layout.addRow("当前任务:", self._reminder_task_label)
        
        # 提醒日期时间
        datetime_layout = QHBoxLayout()
        
        date_label = QLabel("提醒日期:")
        date_label.setStyleSheet("font-weight: normal;")
        datetime_layout.addWidget(date_label)
        
        self._reminder_date = QDateEdit()
        self._reminder_date.setCalendarPopup(True)
        self._reminder_date.setDate(QDate.currentDate())
        self._reminder_date.setStyleSheet("""
            QDateEdit {
                padding: 5px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QDateEdit:hover {
                border-color: #FF9800;
            }
        """)
        datetime_layout.addWidget(self._reminder_date)
        
        time_label = QLabel("提醒时间:")
        time_label.setStyleSheet("font-weight: normal; margin-left: 20px;")
        datetime_layout.addWidget(time_label)
        
        self._reminder_time = QTimeEdit()
        self._reminder_time.setDisplayFormat("HH:mm")
        self._reminder_time.setStyleSheet("""
            QTimeEdit {
                padding: 5px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QTimeEdit:hover {
                border-color: #FF9800;
            }
        """)
        datetime_layout.addWidget(self._reminder_time)
        
        datetime_layout.addStretch()
        settings_layout.addRow(datetime_layout)
        
        # 提醒方式
        method_layout = QHBoxLayout()
        method_label = QLabel("提醒方式:")
        method_label.setStyleSheet("font-weight: normal;")
        method_layout.addWidget(method_label)
        
        self._reminder_method_combo = QComboBox()
        for method_id, method_name in self.REMINDER_METHOD_NAMES.items():
            self._reminder_method_combo.addItem(method_name, method_id)
        self._reminder_method_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #FF9800;
            }
        """)
        method_layout.addWidget(self._reminder_method_combo)
        method_layout.addStretch()
        settings_layout.addRow(method_layout)
        
        # 启用状态
        self._reminder_enabled_check = QCheckBox("启用提醒")
        self._reminder_enabled_check.setChecked(True)
        self._reminder_enabled_check.setStyleSheet("""
            QCheckBox {
                font-weight: normal;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        settings_layout.addRow(self._reminder_enabled_check)
        
        # 保存按钮
        save_reminder_layout = QHBoxLayout()
        save_reminder_layout.addStretch()
        
        save_reminder_btn = QPushButton("保存提醒")
        save_reminder_btn.setMinimumWidth(120)
        save_reminder_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #EF6C00;
            }
        """)
        save_reminder_btn.clicked.connect(self._on_save_reminder)
        save_reminder_layout.addWidget(save_reminder_btn)
        
        settings_layout.addRow(save_reminder_layout)
        
        layout.addWidget(settings_group)
        
        # 已有提醒列表
        reminders_group = QGroupBox("已有提醒")
        reminders_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
                color: #333;
            }
        """)
        
        reminders_layout = QVBoxLayout(reminders_group)
        reminders_layout.setContentsMargins(10, 10, 10, 10)
        reminders_layout.setSpacing(5)
        
        self._existing_reminders_list = QListWidget()
        self._existing_reminders_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background-color: #fafafa;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565C0;
                border: 1px solid #2196F3;
            }
        """)
        self._existing_reminders_list.currentRowChanged.connect(self._on_existing_reminder_selected)
        reminders_layout.addWidget(self._existing_reminders_list)
        
        layout.addWidget(reminders_group, 1)
        
        # 初始化提醒面板
        self._clear_reminder_panel()
        
        return panel
    
    def _create_progress_tracking_tab(self) -> QWidget:
        """
        创建进度追踪标签页
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 统计概览
        overview_group = self._create_progress_overview()
        layout.addWidget(overview_group)
        
        # 学习记录
        records_group = self._create_study_records_panel()
        layout.addWidget(records_group, 1)
        
        # 加载进度数据
        self._load_progress_data()
        
        return widget
    
    def _create_progress_overview(self) -> QGroupBox:
        """
        创建进度统计概览
        """
        group = QGroupBox("学习进度概览")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
                color: #333;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 总学习时间
        self._total_hours_label = QLabel("0 小时")
        self._total_hours_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        total_hours_title = QLabel("总学习时间")
        total_hours_title.setStyleSheet("font-size: 12px; color: #666;")
        
        total_layout = QVBoxLayout()
        total_layout.addWidget(self._total_hours_label)
        total_layout.addWidget(total_hours_title)
        total_frame = QFrame()
        total_frame.setLayout(total_layout)
        total_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        layout.addWidget(total_frame, 0, 0)
        
        # 完成的计划数
        self._completed_plans_label = QLabel("0")
        self._completed_plans_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        completed_plans_title = QLabel("完成的计划")
        completed_plans_title.setStyleSheet("font-size: 12px; color: #666;")
        
        completed_layout = QVBoxLayout()
        completed_layout.addWidget(self._completed_plans_label)
        completed_layout.addWidget(completed_plans_title)
        completed_frame = QFrame()
        completed_frame.setLayout(completed_layout)
        completed_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e9;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        layout.addWidget(completed_frame, 0, 1)
        
        # 进行中的计划
        self._active_plans_label = QLabel("0")
        self._active_plans_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FF9800;")
        active_plans_title = QLabel("进行中的计划")
        active_plans_title.setStyleSheet("font-size: 12px; color: #666;")
        
        active_layout = QVBoxLayout()
        active_layout.addWidget(self._active_plans_label)
        active_layout.addWidget(active_plans_title)
        active_frame = QFrame()
        active_frame.setLayout(active_layout)
        active_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        layout.addWidget(active_frame, 0, 2)
        
        # 总进度条
        progress_layout = QVBoxLayout()
        progress_title = QLabel("总体学习进度")
        progress_title.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 5px;")
        progress_layout.addWidget(progress_title)
        
        self._overall_progress = QProgressBar()
        self._overall_progress.setMinimum(0)
        self._overall_progress.setMaximum(100)
        self._overall_progress.setValue(0)
        self._overall_progress.setFormat("%p%")
        self._overall_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #e0e0e0;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self._overall_progress)
        
        progress_frame = QFrame()
        progress_frame.setLayout(progress_layout)
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        layout.addWidget(progress_frame, 1, 0, 1, 3)
        
        return group
    
    def _create_study_records_panel(self) -> QGroupBox:
        """
        创建学习记录面板
        """
        group = QGroupBox("学习记录")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
                color: #333;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        
        add_record_btn = QPushButton("添加学习记录")
        add_record_btn.setStyleSheet("""
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
        add_record_btn.clicked.connect(self._on_add_study_record)
        toolbar.addWidget(add_record_btn)
        
        delete_record_btn = QPushButton("删除记录")
        delete_record_btn.setStyleSheet("""
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
        delete_record_btn.clicked.connect(self._on_delete_study_record)
        toolbar.addWidget(delete_record_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # 学习记录表格
        self._records_table = QTableWidget()
        self._records_table.setColumnCount(5)
        self._records_table.setHorizontalHeaderLabels(["日期", "计划", "学习时长", "备注", "记录时间"])
        self._records_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._records_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._records_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._records_table.setAlternatingRowColors(True)
        self._records_table.setStyleSheet("""
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
                border: none;
                border-bottom: 2px solid #ddd;
                font-weight: bold;
            }
        """)
        layout.addWidget(self._records_table, 1)
        
        return group
    
    # ==================== 学习计划相关方法 ====================
    
    def _load_study_plans(self, filter_status: int = None):
        """
        加载学习计划列表
        """
        self._plans_list.clear()
        
        if filter_status is None:
            plans = self._db.query_all("""
                SELECT id, title, status, start_date, end_date, completed_hours, total_hours
                FROM study_plans
                ORDER BY created_at DESC
            """)
        else:
            plans = self._db.query_all("""
                SELECT id, title, status, start_date, end_date, completed_hours, total_hours
                FROM study_plans
                WHERE status = ?
                ORDER BY created_at DESC
            """, (filter_status,))
        
        for plan in plans:
            status_text = self.PLAN_STATUS_NAMES.get(plan['status'], "未知")
            
            # 计算进度
            progress = 0
            if plan['total_hours'] > 0:
                progress = (plan['completed_hours'] / plan['total_hours']) * 100
            
            display_text = f"{plan['title']}\n状态: {status_text} | 进度: {progress:.1f}%"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, plan['id'])
            
            # 根据状态设置颜色
            if plan['status'] == self.PLAN_STATUS_COMPLETED:
                item.setForeground(QColor("#4CAF50"))
            elif plan['status'] == self.PLAN_STATUS_IN_PROGRESS:
                item.setForeground(QColor("#2196F3"))
            elif plan['status'] == self.PLAN_STATUS_PAUSED:
                item.setForeground(QColor("#9E9E9E"))
            
            self._plans_list.addItem(item)
    
    def _on_plan_filter_changed(self, index):
        """
        计划筛选条件改变
        """
        filter_status = None if index == 0 else index - 1
        self._load_study_plans(filter_status)
    
    def _on_plan_selected(self, index):
        """
        当选择学习计划时触发
        """
        if index < 0:
            self._clear_plan_detail_panel()
            return
        
        item = self._plans_list.item(index)
        plan_id = item.data(Qt.ItemDataRole.UserRole)
        
        plan = self._db.query_one(
            "SELECT * FROM study_plans WHERE id = ?",
            (plan_id,)
        )
        
        if plan:
            self._current_plan_id = plan_id
            self._plan_title_edit.setPlainText(plan['title'])
            self._plan_description_edit.setPlainText(plan['description'] if plan['description'] else "")
            self._plan_total_hours.setValue(int(plan['total_hours']))
            
            # 设置日期
            if plan['start_date']:
                try:
                    date = QDate.fromString(plan['start_date'], "yyyy-MM-dd")
                    self._plan_start_date.setDate(date)
                except:
                    pass
            
            if plan['end_date']:
                try:
                    date = QDate.fromString(plan['end_date'], "yyyy-MM-dd")
                    self._plan_end_date.setDate(date)
                except:
                    pass
            
            # 设置状态
            status_index = self._plan_status_combo.findData(plan['status'])
            if status_index >= 0:
                self._plan_status_combo.setCurrentIndex(status_index)
            
            # 加载任务列表
            self._load_plan_tasks(plan_id)
    
    def _load_plan_tasks(self, plan_id):
        """
        加载计划的任务列表
        """
        self._tasks_table.setRowCount(0)
        
        tasks = self._db.query_all("""
            SELECT id, title, priority, scheduled_date, estimated_hours, actual_hours, status
            FROM study_tasks
            WHERE plan_id = ?
            ORDER BY scheduled_date ASC, priority DESC
        """, (plan_id,))
        
        for row, task in enumerate(tasks):
            self._tasks_table.insertRow(row)
            
            # 任务标题
            title_item = QTableWidgetItem(task['title'])
            title_item.setData(Qt.ItemDataRole.UserRole, task['id'])
            self._tasks_table.setItem(row, 0, title_item)
            
            # 优先级
            priority_text = self.PRIORITY_NAMES.get(task['priority'], "未知")
            priority_item = QTableWidgetItem(priority_text)
            self._tasks_table.setItem(row, 1, priority_item)
            
            # 计划日期
            date_text = task['scheduled_date'] if task['scheduled_date'] else "未设置"
            date_item = QTableWidgetItem(date_text)
            self._tasks_table.setItem(row, 2, date_item)
            
            # 预估学时
            estimated_item = QTableWidgetItem(f"{task['estimated_hours']}h")
            self._tasks_table.setItem(row, 3, estimated_item)
            
            # 实际学时
            actual_item = QTableWidgetItem(f"{task['actual_hours']}h")
            self._tasks_table.setItem(row, 4, actual_item)
            
            # 状态
            status_text = self.TASK_STATUS_NAMES.get(task['status'], "未知")
            status_item = QTableWidgetItem(status_text)
            
            # 根据状态设置颜色
            if task['status'] == self.TASK_STATUS_COMPLETED:
                status_item.setForeground(QColor("#4CAF50"))
            elif task['status'] == self.TASK_STATUS_IN_PROGRESS:
                status_item.setForeground(QColor("#2196F3"))
            
            self._tasks_table.setItem(row, 5, status_item)
    
    def _clear_plan_detail_panel(self):
        """
        清空计划详情面板
        """
        self._current_plan_id = None
        self._plan_title_edit.clear()
        self._plan_description_edit.clear()
        self._plan_total_hours.setValue(100)
        self._plan_start_date.setDate(QDate.currentDate())
        self._plan_end_date.setDate(QDate.currentDate().addDays(30))
        self._plan_status_combo.setCurrentIndex(0)
        self._tasks_table.setRowCount(0)
    
    def _on_new_study_plan(self):
        """
        创建新学习计划
        """
        title, ok = QInputDialog.getText(
            None, "新建学习计划", "请输入计划标题:"
        )
        
        if ok and title.strip():
            now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            start_date = QDate.currentDate().toString("yyyy-MM-dd")
            end_date = QDate.currentDate().addDays(30).toString("yyyy-MM-dd")
            
            plan_id = self._db.insert('study_plans', {
                'title': title.strip(),
                'description': '',
                'start_date': start_date,
                'end_date': end_date,
                'total_hours': 100,
                'completed_hours': 0,
                'status': self.PLAN_STATUS_NOT_STARTED,
                'created_at': now,
                'updated_at': now
            })
            
            if plan_id > 0:
                current_filter = self._plan_filter_combo.currentIndex()
                filter_status = None if current_filter == 0 else current_filter - 1
                self._load_study_plans(filter_status)
                
                # 选中新创建的计划
                for i in range(self._plans_list.count()):
                    item = self._plans_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == plan_id:
                        self._plans_list.setCurrentRow(i)
                        break
                
                QMessageBox.information(None, "成功", "学习计划创建成功！")
    
    def _on_save_plan(self):
        """
        保存学习计划
        """
        if not hasattr(self, '_current_plan_id') or self._current_plan_id is None:
            QMessageBox.warning(None, "警告", "请先选择或创建一个学习计划！")
            return
        
        title = self._plan_title_edit.toPlainText().strip()
        if not title:
            QMessageBox.warning(None, "警告", "计划标题不能为空！")
            return
        
        description = self._plan_description_edit.toPlainText()
        total_hours = self._plan_total_hours.value()
        status = self._plan_status_combo.currentData()
        start_date = self._plan_start_date.date().toString("yyyy-MM-dd")
        end_date = self._plan_end_date.date().toString("yyyy-MM-dd")
        
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        affected = self._db.update(
            'study_plans',
            {
                'title': title,
                'description': description,
                'start_date': start_date,
                'end_date': end_date,
                'total_hours': total_hours,
                'status': status,
                'updated_at': now
            },
            'id = ?',
            (self._current_plan_id,)
        )
        
        if affected > 0:
            current_filter = self._plan_filter_combo.currentIndex()
            filter_status = None if current_filter == 0 else current_filter - 1
            self._load_study_plans(filter_status)
            
            QMessageBox.information(None, "成功", "学习计划保存成功！")
    
    def _on_delete_plan(self):
        """
        删除学习计划
        """
        current_row = self._plans_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(None, "警告", "请先选择要删除的学习计划！")
            return
        
        item = self._plans_list.item(current_row)
        plan_id = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            None, "确认删除",
            f"确定要删除这个学习计划吗？\n\n注意：该计划下的所有任务也将被删除。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 先删除任务
            self._db.delete('study_tasks', 'plan_id = ?', (plan_id,))
            
            # 删除计划
            affected = self._db.delete('study_plans', 'id = ?', (plan_id,))
            
            if affected > 0:
                current_filter = self._plan_filter_combo.currentIndex()
                filter_status = None if current_filter == 0 else current_filter - 1
                self._load_study_plans(filter_status)
                self._clear_plan_detail_panel()
                
                QMessageBox.information(None, "成功", "学习计划删除成功！")
    
    def _on_new_task(self):
        """
        创建新任务
        """
        if not hasattr(self, '_current_plan_id') or self._current_plan_id is None:
            QMessageBox.warning(None, "警告", "请先选择一个学习计划！")
            return
        
        title, ok = QInputDialog.getText(
            None, "新建任务", "请输入任务标题:"
        )
        
        if ok and title.strip():
            now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            scheduled_date = QDate.currentDate().toString("yyyy-MM-dd")
            
            task_id = self._db.insert('study_tasks', {
                'plan_id': self._current_plan_id,
                'title': title.strip(),
                'description': '',
                'priority': self.PRIORITY_MEDIUM,
                'scheduled_date': scheduled_date,
                'estimated_hours': 1,
                'actual_hours': 0,
                'status': self.TASK_STATUS_NOT_STARTED,
                'created_at': now,
                'updated_at': now
            })
            
            if task_id > 0:
                self._load_plan_tasks(self._current_plan_id)
                QMessageBox.information(None, "成功", "任务创建成功！双击任务可编辑详情。")
    
    def _on_task_double_clicked(self, item):
        """
        双击任务编辑
        """
        row = item.row()
        task_id_item = self._tasks_table.item(row, 0)
        task_id = task_id_item.data(Qt.ItemDataRole.UserRole)
        
        task = self._db.query_one(
            "SELECT * FROM study_tasks WHERE id = ?",
            (task_id,)
        )
        
        if task:
            self._show_task_edit_dialog(task)
    
    def _show_task_edit_dialog(self, task):
        """
        显示任务编辑对话框
        """
        # 这里简化处理，实际可以创建更复杂的对话框
        # 暂时使用输入对话框让用户修改任务状态
        
        status_options = list(self.TASK_STATUS_NAMES.values())
        current_status_name = self.TASK_STATUS_NAMES.get(task['status'], "未开始")
        
        status_name, ok = QInputDialog.getItem(
            None, "编辑任务状态",
            f"任务: {task['title']}\n\n选择新状态:",
            status_options,
            list(self.TASK_STATUS_NAMES.keys()).index(task['status']),
            False
        )
        
        if ok and status_name:
            # 找到对应的状态ID
            status_id = None
            for sid, sname in self.TASK_STATUS_NAMES.items():
                if sname == status_name:
                    status_id = sid
                    break
            
            if status_id is not None:
                now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                
                affected = self._db.update(
                    'study_tasks',
                    {
                        'status': status_id,
                        'updated_at': now
                    },
                    'id = ?',
                    (task['id'],)
                )
                
                if affected > 0:
                    self._load_plan_tasks(task['plan_id'])
                    QMessageBox.information(None, "成功", "任务状态更新成功！")
    
    # ==================== 复习提醒相关方法 ====================
    
    def _load_review_tasks(self):
        """
        加载待复习任务列表
        """
        self._review_tasks_list.clear()
        
        # 查询所有进行中的任务和已完成的任务（需要复习）
        tasks = self._db.query_all("""
            SELECT t.id, t.title, t.status, t.scheduled_date, p.title as plan_title
            FROM study_tasks t
            JOIN study_plans p ON t.plan_id = p.id
            WHERE t.status IN (?, ?)
            ORDER BY t.scheduled_date ASC
        """, (self.TASK_STATUS_IN_PROGRESS, self.TASK_STATUS_COMPLETED))
        
        for task in tasks:
            status_text = self.TASK_STATUS_NAMES.get(task['status'], "未知")
            
            display_text = f"{task['title']}\n计划: {task['plan_title']} | 状态: {status_text}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, task['id'])
            
            self._review_tasks_list.addItem(item)
    
    def _on_review_task_selected(self, index):
        """
        当选择待复习任务时触发
        """
        if index < 0:
            self._clear_reminder_panel()
            return
        
        item = self._review_tasks_list.item(index)
        task_id = item.data(Qt.ItemDataRole.UserRole)
        
        task = self._db.query_one(
            "SELECT * FROM study_tasks WHERE id = ?",
            (task_id,)
        )
        
        if task:
            self._current_review_task_id = task_id
            self._reminder_task_label.setText(task['title'])
            
            # 加载已有提醒
            self._load_existing_reminders(task_id)
    
    def _load_existing_reminders(self, task_id):
        """
        加载任务的已有提醒
        """
        self._existing_reminders_list.clear()
        
        reminders = self._db.query_all("""
            SELECT id, reminder_time, reminder_method, is_enabled, is_sent
            FROM review_reminders
            WHERE task_id = ?
            ORDER BY reminder_time ASC
        """, (task_id,))
        
        for reminder in reminders:
            method_text = self.REMINDER_METHOD_NAMES.get(reminder['reminder_method'], "未知")
            enabled_text = "启用" if reminder['is_enabled'] else "禁用"
            sent_text = "已发送" if reminder['is_sent'] else "未发送"
            
            display_text = f"{reminder['reminder_time']}\n方式: {method_text} | {enabled_text} | {sent_text}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, reminder['id'])
            
            if reminder['is_sent']:
                item.setForeground(QColor("#9E9E9E"))
            elif not reminder['is_enabled']:
                item.setForeground(QColor("#FF9800"))
            
            self._existing_reminders_list.addItem(item)
    
    def _on_existing_reminder_selected(self, index):
        """
        当选择已有提醒时触发
        """
        if index < 0:
            return
        
        item = self._existing_reminders_list.item(index)
        reminder_id = item.data(Qt.ItemDataRole.UserRole)
        
        reminder = self._db.query_one(
            "SELECT * FROM review_reminders WHERE id = ?",
            (reminder_id,)
        )
        
        if reminder:
            self._current_reminder_id = reminder_id
            
            # 解析日期时间
            try:
                datetime = QDateTime.fromString(reminder['reminder_time'], "yyyy-MM-dd hh:mm:ss")
                self._reminder_date.setDate(datetime.date())
                self._reminder_time.setTime(datetime.time())
            except:
                pass
            
            # 设置提醒方式
            method_index = self._reminder_method_combo.findData(reminder['reminder_method'])
            if method_index >= 0:
                self._reminder_method_combo.setCurrentIndex(method_index)
            
            # 设置启用状态
            self._reminder_enabled_check.setChecked(reminder['is_enabled'] == 1)
    
    def _clear_reminder_panel(self):
        """
        清空提醒面板
        """
        self._current_review_task_id = None
        self._current_reminder_id = None
        self._reminder_task_label.setText("未选择任务")
        self._reminder_date.setDate(QDate.currentDate())
        self._reminder_method_combo.setCurrentIndex(0)
        self._reminder_enabled_check.setChecked(True)
        self._existing_reminders_list.clear()
    
    def _on_new_reminder(self):
        """
        创建新提醒
        """
        if not hasattr(self, '_current_review_task_id') or self._current_review_task_id is None:
            QMessageBox.warning(None, "警告", "请先选择一个任务！")
            return
        
        self._current_reminder_id = None
        QMessageBox.information(None, "提示", "请设置提醒时间和方式，然后点击保存提醒按钮。")
    
    def _on_save_reminder(self):
        """
        保存提醒
        """
        if not hasattr(self, '_current_review_task_id') or self._current_review_task_id is None:
            QMessageBox.warning(None, "警告", "请先选择一个任务！")
            return
        
        # 构建提醒时间
        date = self._reminder_date.date()
        time = self._reminder_time.time()
        reminder_datetime = QDateTime(date, time).toString("yyyy-MM-dd hh:mm:ss")
        
        reminder_method = self._reminder_method_combo.currentData()
        is_enabled = 1 if self._reminder_enabled_check.isChecked() else 0
        
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        if hasattr(self, '_current_reminder_id') and self._current_reminder_id is not None:
            # 更新现有提醒
            affected = self._db.update(
                'review_reminders',
                {
                    'reminder_time': reminder_datetime,
                    'reminder_method': reminder_method,
                    'is_enabled': is_enabled,
                    'is_sent': 0
                },
                'id = ?',
                (self._current_reminder_id,)
            )
        else:
            # 创建新提醒
            affected = self._db.insert('review_reminders', {
                'task_id': self._current_review_task_id,
                'reminder_time': reminder_datetime,
                'reminder_method': reminder_method,
                'is_enabled': is_enabled,
                'is_sent': 0,
                'created_at': now
            })
            affected = 1 if affected > 0 else 0
        
        if affected > 0:
            self._load_existing_reminders(self._current_review_task_id)
            QMessageBox.information(None, "成功", "提醒保存成功！")
    
    def _on_delete_reminder(self):
        """
        删除提醒
        """
        current_row = self._existing_reminders_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(None, "警告", "请先选择要删除的提醒！")
            return
        
        item = self._existing_reminders_list.item(current_row)
        reminder_id = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            None, "确认删除",
            "确定要删除这个提醒吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            affected = self._db.delete('review_reminders', 'id = ?', (reminder_id,))
            
            if affected > 0:
                self._load_existing_reminders(self._current_review_task_id)
                QMessageBox.information(None, "成功", "提醒删除成功！")
    
    # ==================== 进度追踪相关方法 ====================
    
    def _load_progress_data(self):
        """
        加载进度数据
        """
        # 计算总学习时间
        total_hours = self._db.query_scalar("""
            SELECT COALESCE(SUM(hours_studied), 0) FROM study_progress
        """)
        self._total_hours_label.setText(f"{total_hours:.1f} 小时")
        
        # 计算完成的计划数
        completed_plans = self._db.query_scalar("""
            SELECT COUNT(*) FROM study_plans WHERE status = ?
        """, (self.PLAN_STATUS_COMPLETED,))
        self._completed_plans_label.setText(str(completed_plans))
        
        # 计算进行中的计划数
        active_plans = self._db.query_scalar("""
            SELECT COUNT(*) FROM study_plans WHERE status = ?
        """, (self.PLAN_STATUS_IN_PROGRESS,))
        self._active_plans_label.setText(str(active_plans))
        
        # 计算总体进度
        total_planned_hours = self._db.query_scalar("""
            SELECT COALESCE(SUM(total_hours), 0) FROM study_plans
        """)
        total_completed_hours = self._db.query_scalar("""
            SELECT COALESCE(SUM(completed_hours), 0) FROM study_plans
        """)
        
        if total_planned_hours > 0:
            overall_progress = (total_completed_hours / total_planned_hours) * 100
            self._overall_progress.setValue(int(overall_progress))
        else:
            self._overall_progress.setValue(0)
        
        # 加载学习记录
        self._load_study_records()
    
    def _load_study_records(self):
        """
        加载学习记录
        """
        self._records_table.setRowCount(0)
        
        records = self._db.query_all("""
            SELECT sp.id, sp.study_date, sp.hours_studied, sp.notes, 
                   sp.created_at, p.title as plan_title
            FROM study_progress sp
            LEFT JOIN study_plans p ON sp.plan_id = p.id
            ORDER BY sp.study_date DESC
        """)
        
        for row, record in enumerate(records):
            self._records_table.insertRow(row)
            
            # 日期
            date_item = QTableWidgetItem(record['study_date'])
            date_item.setData(Qt.ItemDataRole.UserRole, record['id'])
            self._records_table.setItem(row, 0, date_item)
            
            # 计划
            plan_title = record['plan_title'] if record['plan_title'] else "无计划"
            plan_item = QTableWidgetItem(plan_title)
            self._records_table.setItem(row, 1, plan_item)
            
            # 学习时长
            hours_item = QTableWidgetItem(f"{record['hours_studied']}h")
            self._records_table.setItem(row, 2, hours_item)
            
            # 备注
            notes = record['notes'] if record['notes'] else ""
            notes_item = QTableWidgetItem(notes)
            self._records_table.setItem(row, 3, notes_item)
            
            # 记录时间
            time_item = QTableWidgetItem(record['created_at'])
            self._records_table.setItem(row, 4, time_item)
    
    def _on_add_study_record(self):
        """
        添加学习记录
        """
        # 先获取所有计划
        plans = self._db.query_all("""
            SELECT id, title FROM study_plans WHERE status IN (?, ?)
        """, (self.PLAN_STATUS_NOT_STARTED, self.PLAN_STATUS_IN_PROGRESS))
        
        plan_options = ["无计划"] + [p['title'] for p in plans]
        
        # 选择计划
        plan_name, ok = QInputDialog.getItem(
            None, "添加学习记录",
            "选择关联的计划:",
            plan_options, 0, False
        )
        
        if not ok:
            return
        
        # 输入学习时长
        hours_text, ok = QInputDialog.getText(
            None, "添加学习记录",
            "请输入学习时长（小时）:"
        )
        
        if not ok or not hours_text.strip():
            return
        
        try:
            hours = float(hours_text.strip())
            if hours <= 0:
                raise ValueError("时长必须大于0")
        except ValueError:
            QMessageBox.warning(None, "警告", "请输入有效的学习时长！")
            return
        
        # 输入备注
        notes, ok = QInputDialog.getText(
            None, "添加学习记录",
            "学习备注（可选）:"
        )
        
        if not ok:
            return
        
        # 确定计划ID
        plan_id = None
        if plan_name != "无计划":
            for plan in plans:
                if plan['title'] == plan_name:
                    plan_id = plan['id']
                    break
        
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        study_date = QDate.currentDate().toString("yyyy-MM-dd")
        
        # 插入学习记录
        record_id = self._db.insert('study_progress', {
            'plan_id': plan_id,
            'task_id': None,
            'study_date': study_date,
            'hours_studied': hours,
            'notes': notes if notes else None,
            'created_at': now
        })
        
        if record_id > 0:
            # 如果有关联计划，更新计划的已完成学时
            if plan_id:
                # 获取当前计划的已完成学时
                current_completed = self._db.query_scalar("""
                    SELECT completed_hours FROM study_plans WHERE id = ?
                """, (plan_id,))
                
                new_completed = current_completed + hours
                
                self._db.update(
                    'study_plans',
                    {'completed_hours': new_completed},
                    'id = ?',
                    (plan_id,)
                )
            
            # 重新加载数据
            self._load_progress_data()
            QMessageBox.information(None, "成功", "学习记录添加成功！")
    
    def _on_delete_study_record(self):
        """
        删除学习记录
        """
        current_row = self._records_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(None, "警告", "请先选择要删除的学习记录！")
            return
        
        item = self._records_table.item(current_row, 0)
        record_id = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            None, "确认删除",
            "确定要删除这条学习记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 获取记录信息，以便更新计划学时
            record = self._db.query_one(
                "SELECT * FROM study_progress WHERE id = ?",
                (record_id,)
            )
            
            if record:
                # 删除记录
                affected = self._db.delete('study_progress', 'id = ?', (record_id,))
                
                if affected > 0:
                    # 如果有关联计划，更新计划的已完成学时
                    if record['plan_id']:
                        # 获取当前计划的已完成学时
                        current_completed = self._db.query_scalar("""
                            SELECT completed_hours FROM study_plans WHERE id = ?
                        """, (record['plan_id'],))
                        
                        new_completed = max(0, current_completed - record['hours_studied'])
                        
                        self._db.update(
                            'study_plans',
                            {'completed_hours': new_completed},
                            'id = ?',
                            (record['plan_id'],)
                        )
                    
                    # 重新加载数据
                    self._load_progress_data()
                    QMessageBox.information(None, "成功", "学习记录删除成功！")
