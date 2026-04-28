#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据备份恢复模块
提供数据库备份、恢复和备份历史管理功能
"""

import os
import shutil
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem, QFileDialog,
                             QMessageBox, QGroupBox, QFormLayout, QCheckBox,
                             QSpinBox, QComboBox, QTabWidget, QTextEdit,
                             QSplitter, QProgressBar, QFrame)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QBrush

from modules.module_manager import BaseModule, ModuleCategory
from database.database_manager import DatabaseManager


class DataBackupModule(BaseModule):
    """
    数据备份恢复模块
    提供数据库备份、恢复和备份历史管理功能
    """
    
    @property
    def module_id(self) -> str:
        return "data_backup"
    
    @property
    def name(self) -> str:
        return "数据备份恢复"
    
    @property
    def description(self) -> str:
        return "数据库备份和恢复工具，支持手动备份、自动备份和备份历史管理"
    
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
        self._create_backup_table()
        self._load_settings()
        self._auto_backup_timer = None
        self._setup_auto_backup()
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        if self._auto_backup_timer:
            self._auto_backup_timer.stop()
    
    def _create_backup_table(self):
        """
        创建备份历史记录表
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS backup_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_name TEXT NOT NULL,
            backup_path TEXT NOT NULL,
            backup_type TEXT DEFAULT 'manual',
            backup_size INTEGER DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self._db.execute(create_table_sql)
        
        create_index_sql = "CREATE INDEX IF NOT EXISTS idx_backup_history_created_at ON backup_history(created_at)"
        self._db.execute(create_index_sql)
    
    def _load_settings(self):
        """
        加载备份设置
        """
        self._backup_dir = self._db.get_setting(
            "backup_dir",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups"),
            self.module_id
        )
        self._auto_backup_enabled = self._db.get_setting(
            "auto_backup_enabled", "false", self.module_id
        ).lower() == "true"
        self._auto_backup_interval = int(self._db.get_setting(
            "auto_backup_interval", "24", self.module_id
        ))
        self._max_backups = int(self._db.get_setting(
            "max_backups", "10", self.module_id
        ))
    
    def _save_settings(self):
        """
        保存备份设置
        """
        self._db.set_setting("backup_dir", self._backup_dir, self.module_id)
        self._db.set_setting("auto_backup_enabled", str(self._auto_backup_enabled).lower(), self.module_id)
        self._db.set_setting("auto_backup_interval", str(self._auto_backup_interval), self.module_id)
        self._db.set_setting("max_backups", str(self._max_backups), self.module_id)
    
    def _setup_auto_backup(self):
        """
        设置自动备份
        """
        if self._auto_backup_timer:
            self._auto_backup_timer.stop()
        
        if self._auto_backup_enabled:
            self._auto_backup_timer = QTimer()
            self._auto_backup_timer.timeout.connect(self._perform_auto_backup)
            interval_ms = self._auto_backup_interval * 60 * 60 * 1000
            self._auto_backup_timer.start(interval_ms)
    
    def _perform_auto_backup(self):
        """
        执行自动备份
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"auto_backup_{timestamp}"
        description = f"自动备份 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        success, message = self._create_backup(backup_name, "auto", description)
        
        if success:
            self._cleanup_old_backups()
    
    def _create_backup(self, backup_name: str, backup_type: str = "manual", 
                       description: str = "") -> tuple:
        """
        创建数据库备份
        返回 (success: bool, message: str)
        """
        try:
            os.makedirs(self._backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in backup_name if c.isalnum() or c in ('_', '-', ' '))
            backup_filename = f"{safe_name}_{timestamp}.db"
            backup_path = os.path.join(self._backup_dir, backup_filename)
            
            source_db_path = self._db.db_path
            
            shutil.copy2(source_db_path, backup_path)
            
            backup_size = os.path.getsize(backup_path)
            
            self._db.insert('backup_history', {
                'backup_name': backup_name,
                'backup_path': backup_path,
                'backup_type': backup_type,
                'backup_size': backup_size,
                'description': description,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            return True, f"备份创建成功: {backup_filename}"
            
        except Exception as e:
            return False, f"备份创建失败: {str(e)}"
    
    def _restore_backup(self, backup_path: str) -> tuple:
        """
        从备份恢复数据库
        返回 (success: bool, message: str)
        """
        try:
            if not os.path.exists(backup_path):
                return False, "备份文件不存在"
            
            if not self._verify_backup(backup_path):
                return False, "备份文件验证失败，可能已损坏"
            
            source_db_path = self._db.db_path
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            restore_backup_path = f"{source_db_path}.before_restore_{timestamp}"
            shutil.copy2(source_db_path, restore_backup_path)
            
            self._db.close()
            
            shutil.copy2(backup_path, source_db_path)
            
            DatabaseManager._instance = None
            self._db = DatabaseManager()
            
            return True, "数据库恢复成功！\n应用已自动重新连接到恢复后的数据库。\n\n" \
                         f"注意：恢复前的数据库已备份到: {restore_backup_path}"
            
        except Exception as e:
            try:
                DatabaseManager._instance = None
                self._db = DatabaseManager()
            except:
                pass
            return False, f"恢复失败: {str(e)}"
    
    def _verify_backup(self, backup_path: str) -> bool:
        """
        验证备份文件是否有效
        """
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            return len(tables) > 0
        except:
            return False
    
    def _delete_backup(self, backup_id: int) -> tuple:
        """
        删除备份记录和文件
        返回 (success: bool, message: str)
        """
        try:
            backup = self._db.query_one(
                "SELECT backup_path FROM backup_history WHERE id = ?",
                (backup_id,)
            )
            
            if not backup:
                return False, "备份记录不存在"
            
            backup_path = backup['backup_path']
            
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            self._db.delete('backup_history', 'id = ?', (backup_id,))
            
            return True, "备份已删除"
            
        except Exception as e:
            return False, f"删除失败: {str(e)}"
    
    def _cleanup_old_backups(self):
        """
        清理旧的备份文件，保留最新的 N 个
        """
        try:
            backups = self._db.query_all(
                "SELECT id, backup_path FROM backup_history ORDER BY created_at ASC"
            )
            
            if len(backups) > self._max_backups:
                to_delete = backups[:len(backups) - self._max_backups]
                
                for backup in to_delete:
                    if os.path.exists(backup['backup_path']):
                        try:
                            os.remove(backup['backup_path'])
                        except:
                            pass
                    self._db.delete('backup_history', 'id = ?', (backup['id'],))
                    
        except Exception as e:
            print(f"清理旧备份失败: {e}")
    
    def _get_backup_list(self) -> List[Dict[str, Any]]:
        """
        获取备份列表
        """
        return self._db.query_all(
            "SELECT * FROM backup_history ORDER BY created_at DESC"
        )
    
    def _format_file_size(self, size: int) -> str:
        """
        格式化文件大小
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    
    def _create_widget(self) -> QWidget:
        """
        创建数据备份恢复模块的主界面
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
        
        backup_tab = self._create_backup_tab()
        restore_tab = self._create_restore_tab()
        settings_tab = self._create_settings_tab()
        
        self._tab_widget.addTab(backup_tab, "💾 备份")
        self._tab_widget.addTab(restore_tab, "🔄 恢复")
        self._tab_widget.addTab(settings_tab, "⚙️ 设置")
        
        main_layout.addWidget(self._tab_widget, 1)
        
        return widget
    
    def _create_backup_tab(self) -> QWidget:
        """
        创建备份选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        title_label = QLabel("数据备份")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        layout.addWidget(title_label)
        
        info_group = QGroupBox("数据库信息")
        info_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        info_group.setStyleSheet("""
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
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(10)
        
        db_path = self._db.db_path
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        
        db_info = QLabel(f"""
            <b>数据库路径:</b> {db_path}<br>
            <b>数据库大小:</b> {self._format_file_size(db_size)}<br>
            <b>备份目录:</b> {self._backup_dir}
        """)
        db_info.setFont(QFont("Microsoft YaHei", 10))
        db_info.setStyleSheet("color: #333; line-height: 1.5;")
        info_layout.addWidget(db_info)
        
        layout.addWidget(info_group)
        
        backup_group = QGroupBox("创建备份")
        backup_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        backup_group.setStyleSheet("""
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
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setSpacing(15)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        from PyQt6.QtWidgets import QLineEdit
        
        self._backup_name_edit = QLineEdit()
        self._backup_name_edit.setPlaceholderText("例如: 2024年数据备份")
        self._backup_name_edit.setFont(QFont("Microsoft YaHei", 10))
        self._backup_name_edit.setMinimumHeight(35)
        self._backup_name_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
            }
        """)
        form_layout.addRow("备份名称:", self._backup_name_edit)
        
        self._backup_desc_edit = QTextEdit()
        self._backup_desc_edit.setPlaceholderText("添加备份描述（可选）...")
        self._backup_desc_edit.setFont(QFont("Microsoft YaHei", 10))
        self._backup_desc_edit.setMaximumHeight(80)
        self._backup_desc_edit.setStyleSheet("""
            QTextEdit {
                padding: 6px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #1565C0;
            }
        """)
        form_layout.addRow("备份描述:", self._backup_desc_edit)
        
        backup_layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self._create_backup_btn = QPushButton("💾 立即备份")
        self._create_backup_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._create_backup_btn.setMinimumHeight(45)
        self._create_backup_btn.setStyleSheet("""
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
        self._create_backup_btn.clicked.connect(self._on_create_backup)
        btn_layout.addWidget(self._create_backup_btn)
        
        btn_layout.addStretch()
        
        backup_layout.addLayout(btn_layout)
        
        layout.addWidget(backup_group)
        
        self._backup_status_label = QLabel("就绪")
        self._backup_status_label.setFont(QFont("Microsoft YaHei", 10))
        self._backup_status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self._backup_status_label)
        
        layout.addStretch()
        
        return tab
    
    def _create_restore_tab(self) -> QWidget:
        """
        创建恢复选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        title_label = QLabel("数据恢复")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        layout.addWidget(title_label)
        
        warning_label = QLabel("⚠️ 警告：恢复操作将覆盖当前数据库！建议先创建备份。")
        warning_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        warning_label.setStyleSheet("color: #f44336; background-color: #ffebee; padding: 10px; border-radius: 4px;")
        layout.addWidget(warning_label)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(5)
        
        list_title = QLabel("备份历史")
        list_title.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        list_title.setStyleSheet("color: #333;")
        list_layout.addWidget(list_title)
        
        self._backup_list = QListWidget()
        self._backup_list.setFont(QFont("Microsoft YaHei", 10))
        self._backup_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px;
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
        self._backup_list.currentRowChanged.connect(self._on_backup_selected)
        list_layout.addWidget(self._backup_list, 1)
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(5)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFont(QFont("Microsoft YaHei", 9))
        refresh_btn.setMinimumHeight(30)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_backup_list)
        btn_row.addWidget(refresh_btn)
        
        import_btn = QPushButton("📂 导入备份")
        import_btn.setFont(QFont("Microsoft YaHei", 9))
        import_btn.setMinimumHeight(30)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        import_btn.clicked.connect(self._on_import_backup)
        btn_row.addWidget(import_btn)
        
        btn_row.addStretch()
        
        list_layout.addLayout(btn_row)
        
        splitter.addWidget(list_panel)
        
        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(5)
        
        detail_title = QLabel("备份详情")
        detail_title.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        detail_title.setStyleSheet("color: #333;")
        detail_layout.addWidget(detail_title)
        
        self._backup_detail_text = QTextEdit()
        self._backup_detail_text.setFont(QFont("Microsoft YaHei", 10))
        self._backup_detail_text.setReadOnly(True)
        self._backup_detail_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                background-color: #fafafa;
            }
        """)
        detail_layout.addWidget(self._backup_detail_text, 1)
        
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        
        self._restore_btn = QPushButton("🔄 恢复此备份")
        self._restore_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self._restore_btn.setMinimumHeight(40)
        self._restore_btn.setEnabled(False)
        self._restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #9E9E9E;
            }
        """)
        self._restore_btn.clicked.connect(self._on_restore_backup)
        action_row.addWidget(self._restore_btn)
        
        self._delete_backup_btn = QPushButton("🗑️ 删除备份")
        self._delete_backup_btn.setFont(QFont("Microsoft YaHei", 10))
        self._delete_backup_btn.setMinimumHeight(40)
        self._delete_backup_btn.setEnabled(False)
        self._delete_backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #9E9E9E;
            }
        """)
        self._delete_backup_btn.clicked.connect(self._on_delete_backup)
        action_row.addWidget(self._delete_backup_btn)
        
        action_row.addStretch()
        
        detail_layout.addLayout(action_row)
        
        splitter.addWidget(detail_panel)
        splitter.setSizes([350, 450])
        
        layout.addWidget(splitter, 1)
        
        self._refresh_backup_list()
        
        return tab
    
    def _create_settings_tab(self) -> QWidget:
        """
        创建设置选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        title_label = QLabel("备份设置")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        layout.addWidget(title_label)
        
        settings_group = QGroupBox("备份设置")
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
        settings_layout.setSpacing(15)
        
        from PyQt6.QtWidgets import QLineEdit
        
        dir_row = QHBoxLayout()
        dir_row.setSpacing(10)
        
        dir_label = QLabel("备份目录:")
        dir_label.setFont(QFont("Microsoft YaHei", 10))
        dir_row.addWidget(dir_label)
        
        self._backup_dir_edit = QLineEdit()
        self._backup_dir_edit.setText(self._backup_dir)
        self._backup_dir_edit.setFont(QFont("Microsoft YaHei", 10))
        self._backup_dir_edit.setMinimumHeight(35)
        self._backup_dir_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1565C0;
            }
        """)
        dir_row.addWidget(self._backup_dir_edit, 1)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.setFont(QFont("Microsoft YaHei", 10))
        browse_btn.setMinimumHeight(35)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        browse_btn.clicked.connect(self._on_browse_backup_dir)
        dir_row.addWidget(browse_btn)
        
        settings_layout.addLayout(dir_row)
        
        auto_backup_row = QHBoxLayout()
        auto_backup_row.setSpacing(10)
        
        self._auto_backup_check = QCheckBox("启用自动备份")
        self._auto_backup_check.setFont(QFont("Microsoft YaHei", 10))
        self._auto_backup_check.setChecked(self._auto_backup_enabled)
        self._auto_backup_check.setStyleSheet("""
            QCheckBox {
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        auto_backup_row.addWidget(self._auto_backup_check)
        
        interval_label = QLabel("备份间隔 (小时):")
        interval_label.setFont(QFont("Microsoft YaHei", 10))
        auto_backup_row.addWidget(interval_label)
        
        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 168)
        self._interval_spin.setValue(self._auto_backup_interval)
        self._interval_spin.setFont(QFont("Microsoft YaHei", 10))
        self._interval_spin.setMinimumHeight(35)
        self._interval_spin.setStyleSheet("""
            QSpinBox {
                padding: 6px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        auto_backup_row.addWidget(self._interval_spin)
        
        auto_backup_row.addStretch()
        
        settings_layout.addLayout(auto_backup_row)
        
        max_backups_row = QHBoxLayout()
        max_backups_row.setSpacing(10)
        
        max_label = QLabel("保留备份数量:")
        max_label.setFont(QFont("Microsoft YaHei", 10))
        max_backups_row.addWidget(max_label)
        
        self._max_backups_spin = QSpinBox()
        self._max_backups_spin.setRange(1, 100)
        self._max_backups_spin.setValue(self._max_backups)
        self._max_backups_spin.setFont(QFont("Microsoft YaHei", 10))
        self._max_backups_spin.setMinimumHeight(35)
        self._max_backups_spin.setStyleSheet("""
            QSpinBox {
                padding: 6px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        max_backups_row.addWidget(self._max_backups_spin)
        
        max_info = QLabel("(超过此数量的旧备份将被自动删除)")
        max_info.setFont(QFont("Microsoft YaHei", 9))
        max_info.setStyleSheet("color: #666;")
        max_backups_row.addWidget(max_info)
        
        max_backups_row.addStretch()
        
        settings_layout.addLayout(max_backups_row)
        
        layout.addWidget(settings_group)
        
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
        self._save_settings_btn.clicked.connect(self._on_save_settings)
        save_row.addWidget(self._save_settings_btn)
        
        save_row.addStretch()
        
        layout.addLayout(save_row)
        
        layout.addStretch()
        
        return tab
    
    def _refresh_backup_list(self):
        """
        刷新备份列表
        """
        self._backup_list.clear()
        
        backups = self._get_backup_list()
        
        if not backups:
            item = QListWidgetItem("暂无备份记录")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._backup_list.addItem(item)
            self._restore_btn.setEnabled(False)
            self._delete_backup_btn.setEnabled(False)
            return
        
        for backup in backups:
            backup_type = "自动" if backup['backup_type'] == 'auto' else "手动"
            type_icon = "🔄" if backup['backup_type'] == 'auto' else "💾"
            
            display_text = f"{type_icon} {backup['backup_name']}\n"
            display_text += f"   {backup['created_at']} | {self._format_file_size(backup['backup_size'])} | {backup_type}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, backup['id'])
            item.setData(Qt.ItemDataRole.UserRole + 1, backup)
            
            if backup['backup_type'] == 'auto':
                item.setForeground(QBrush(QColor("#666666")))
            
            self._backup_list.addItem(item)
        
        self._restore_btn.setEnabled(False)
        self._delete_backup_btn.setEnabled(False)
        self._backup_detail_text.clear()
    
    def _on_backup_selected(self, index):
        """
        当选择备份时触发
        """
        if index < 0:
            self._restore_btn.setEnabled(False)
            self._delete_backup_btn.setEnabled(False)
            self._backup_detail_text.clear()
            return
        
        item = self._backup_list.item(index)
        if not item or "暂无备份记录" in item.text():
            return
        
        backup = item.data(Qt.ItemDataRole.UserRole + 1)
        if not backup:
            return
        
        self._selected_backup_id = backup['id']
        self._selected_backup_path = backup['backup_path']
        
        detail_text = f"""
<b>备份名称:</b> {backup['backup_name']}

<b>备份类型:</b> {'自动备份' if backup['backup_type'] == 'auto' else '手动备份'}

<b>备份时间:</b> {backup['created_at']}

<b>文件大小:</b> {self._format_file_size(backup['backup_size'])}

<b>文件路径:</b> {backup['backup_path']}
"""
        if backup['description']:
            detail_text += f"\n<b>描述:</b> {backup['description']}"
        
        file_exists = os.path.exists(backup['backup_path'])
        detail_text += f"\n\n<b>文件状态:</b> {'存在 ✓' if file_exists else '不存在 ✗'}"
        
        if file_exists:
            is_valid = self._verify_backup(backup['backup_path'])
            detail_text += f"\n<b>验证状态:</b> {'有效 ✓' if is_valid else '损坏 ✗'}"
        
        self._backup_detail_text.setHtml(detail_text.replace('\n', '<br>'))
        
        self._restore_btn.setEnabled(file_exists)
        self._delete_backup_btn.setEnabled(True)
    
    def _on_create_backup(self):
        """
        创建备份按钮点击
        """
        backup_name = self._backup_name_edit.text().strip()
        if not backup_name:
            backup_name = f"手动备份_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        description = self._backup_desc_edit.toPlainText().strip()
        
        self._create_backup_btn.setEnabled(False)
        self._backup_status_label.setText("正在创建备份...")
        
        success, message = self._create_backup(backup_name, "manual", description)
        
        self._create_backup_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(None, "成功", message)
            self._backup_status_label.setText(message)
            self._backup_name_edit.clear()
            self._backup_desc_edit.clear()
            self._refresh_backup_list()
        else:
            QMessageBox.critical(None, "错误", message)
            self._backup_status_label.setText(message)
    
    def _on_restore_backup(self):
        """
        恢复备份按钮点击
        """
        if not hasattr(self, '_selected_backup_id'):
            return
        
        backup = self._db.query_one(
            "SELECT * FROM backup_history WHERE id = ?",
            (self._selected_backup_id,)
        )
        
        if not backup:
            return
        
        reply = QMessageBox.question(
            None, "确认恢复",
            f"确定要从备份 \"{backup['backup_name']}\" 恢复吗？\n\n"
            f"⚠️ 此操作将覆盖当前数据库！\n"
            f"恢复时间: {backup['created_at']}\n\n"
            f"建议：恢复前先创建一个当前状态的备份。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self._restore_backup(backup['backup_path'])
            
            if success:
                QMessageBox.information(None, "成功", message)
                self._refresh_backup_list()
            else:
                QMessageBox.critical(None, "错误", message)
    
    def _on_delete_backup(self):
        """
        删除备份按钮点击
        """
        if not hasattr(self, '_selected_backup_id'):
            return
        
        backup = self._db.query_one(
            "SELECT backup_name FROM backup_history WHERE id = ?",
            (self._selected_backup_id,)
        )
        
        if not backup:
            return
        
        reply = QMessageBox.question(
            None, "确认删除",
            f"确定要删除备份 \"{backup['backup_name']}\" 吗？\n"
            f"此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self._delete_backup(self._selected_backup_id)
            
            if success:
                QMessageBox.information(None, "成功", message)
                self._refresh_backup_list()
            else:
                QMessageBox.critical(None, "错误", message)
    
    def _on_import_backup(self):
        """
        导入备份按钮点击
        """
        file_path, _ = QFileDialog.getOpenFileName(
            None, "选择备份文件", "",
            "SQLite数据库 (*.db);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        if not self._verify_backup(file_path):
            QMessageBox.warning(None, "警告", "选择的文件不是有效的SQLite数据库备份！")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"导入备份_{timestamp}"
        description = f"从外部文件导入: {os.path.basename(file_path)}"
        
        try:
            os.makedirs(self._backup_dir, exist_ok=True)
            backup_filename = f"imported_{timestamp}.db"
            backup_path = os.path.join(self._backup_dir, backup_filename)
            
            shutil.copy2(file_path, backup_path)
            
            backup_size = os.path.getsize(backup_path)
            
            self._db.insert('backup_history', {
                'backup_name': backup_name,
                'backup_path': backup_path,
                'backup_type': 'imported',
                'backup_size': backup_size,
                'description': description,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            QMessageBox.information(None, "成功", "备份导入成功！")
            self._refresh_backup_list()
            
        except Exception as e:
            QMessageBox.critical(None, "错误", f"导入失败: {str(e)}")
    
    def _on_browse_backup_dir(self):
        """
        浏览备份目录按钮点击
        """
        directory = QFileDialog.getExistingDirectory(
            None, "选择备份目录",
            self._backup_dir_edit.text()
        )
        
        if directory:
            self._backup_dir_edit.setText(directory)
    
    def _on_save_settings(self):
        """
        保存设置按钮点击
        """
        self._backup_dir = self._backup_dir_edit.text().strip()
        self._auto_backup_enabled = self._auto_backup_check.isChecked()
        self._auto_backup_interval = self._interval_spin.value()
        self._max_backups = self._max_backups_spin.value()
        
        if not self._backup_dir:
            QMessageBox.warning(None, "警告", "请输入有效的备份目录！")
            return
        
        self._save_settings()
        self._setup_auto_backup()
        
        QMessageBox.information(None, "成功", "设置已保存！")
