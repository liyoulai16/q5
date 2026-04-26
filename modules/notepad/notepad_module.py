#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记事本模块
一个简单的文本编辑器工具
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QFileDialog, QMessageBox, QLabel,
                             QSplitter, QListWidget, QListWidgetItem, QInputDialog)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont

from modules.module_manager import BaseModule
from database.database_manager import DatabaseManager


class NotepadModule(BaseModule):
    """
    记事本模块
    提供文本编辑和笔记管理功能
    """
    
    @property
    def module_id(self) -> str:
        return "notepad"
    
    @property
    def name(self) -> str:
        return "记事本"
    
    @property
    def description(self) -> str:
        return "一个简单的文本编辑器，支持创建、编辑和保存文本文件"
    
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
        self._create_notes_table()
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        pass
    
    def _create_notes_table(self):
        """
        创建笔记数据表
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self._db.execute(create_table_sql)
    
    def _create_widget(self) -> QWidget:
        """
        创建记事本的主界面
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        content_splitter = QSplitter(Qt.Horizontal)
        
        notes_list_panel = self._create_notes_list_panel()
        content_splitter.addWidget(notes_list_panel)
        
        editor_panel = self._create_editor_panel()
        content_splitter.addWidget(editor_panel)
        
        content_splitter.setSizes([250, 750])
        
        main_layout.addWidget(content_splitter)
        
        self._load_notes_list()
        
        return widget
    
    def _create_toolbar(self) -> QWidget:
        """
        创建工具栏
        """
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        new_btn = QPushButton("新建笔记")
        new_btn.clicked.connect(self._on_new_note)
        layout.addWidget(new_btn)
        
        save_btn = QPushButton("保存笔记")
        save_btn.clicked.connect(self._on_save_note)
        layout.addWidget(save_btn)
        
        delete_btn = QPushButton("删除笔记")
        delete_btn.clicked.connect(self._on_delete_note)
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        export_btn = QPushButton("导出文件")
        export_btn.clicked.connect(self._on_export_file)
        layout.addWidget(export_btn)
        
        import_btn = QPushButton("导入文件")
        import_btn.clicked.connect(self._on_import_file)
        layout.addWidget(import_btn)
        
        return toolbar
    
    def _create_notes_list_panel(self) -> QWidget:
        """
        创建笔记列表面板
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        title_label = QLabel("笔记列表")
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        self.notes_list = QListWidget()
        self.notes_list.currentRowChanged.connect(self._on_note_selected)
        layout.addWidget(self.notes_list)
        
        return panel
    
    def _create_editor_panel(self) -> QWidget:
        """
        创建编辑器面板
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.note_title_label = QLabel("未选择笔记")
        self.note_title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        layout.addWidget(self.note_title_label)
        
        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Microsoft YaHei", 11))
        self.text_editor.setPlaceholderText("在此输入文本内容...")
        layout.addWidget(self.text_editor)
        
        return panel
    
    def _load_notes_list(self):
        """
        加载笔记列表
        """
        self.notes_list.clear()
        
        notes = self._db.query_all(
            "SELECT id, title, updated_at FROM notes ORDER BY updated_at DESC"
        )
        
        for note in notes:
            item = QListWidgetItem(note['title'])
            item.setData(Qt.UserRole, note['id'])
            item.setToolTip(f"最后更新: {note['updated_at']}")
            self.notes_list.addItem(item)
    
    def _on_note_selected(self, index):
        """
        当选择笔记时触发
        """
        if index < 0:
            self._clear_editor()
            return
        
        item = self.notes_list.item(index)
        note_id = item.data(Qt.UserRole)
        
        note = self._db.query_one(
            "SELECT id, title, content FROM notes WHERE id = ?",
            (note_id,)
        )
        
        if note:
            self._current_note_id = note_id
            self.note_title_label.setText(note['title'])
            self.text_editor.setPlainText(note['content'] if note['content'] else "")
    
    def _clear_editor(self):
        """
        清空编辑器
        """
        self._current_note_id = None
        self.note_title_label.setText("未选择笔记")
        self.text_editor.clear()
    
    def _on_new_note(self):
        """
        创建新笔记
        """
        title, ok = QInputDialog.getText(
            None, "新建笔记", "请输入笔记标题:"
        )
        
        if ok and title.strip():
            now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            
            note_id = self._db.insert('notes', {
                'title': title.strip(),
                'content': '',
                'created_at': now,
                'updated_at': now
            })
            
            if note_id > 0:
                self._load_notes_list()
                
                for i in range(self.notes_list.count()):
                    item = self.notes_list.item(i)
                    if item.data(Qt.UserRole) == note_id:
                        self.notes_list.setCurrentRow(i)
                        break
                
                QMessageBox.information(None, "成功", "笔记创建成功！")
    
    def _on_save_note(self):
        """
        保存笔记
        """
        if not hasattr(self, '_current_note_id') or self._current_note_id is None:
            QMessageBox.warning(None, "警告", "请先选择或创建一个笔记！")
            return
        
        content = self.text_editor.toPlainText()
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        affected = self._db.update(
            'notes',
            {'content': content, 'updated_at': now},
            'id = ?',
            (self._current_note_id,)
        )
        
        if affected > 0:
            self._load_notes_list()
            QMessageBox.information(None, "成功", "笔记保存成功！")
    
    def _on_delete_note(self):
        """
        删除笔记
        """
        current_row = self.notes_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(None, "警告", "请先选择要删除的笔记！")
            return
        
        item = self.notes_list.item(current_row)
        note_id = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            None, "确认删除",
            f"确定要删除笔记 \"{item.text()}\" 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            affected = self._db.delete('notes', 'id = ?', (note_id,))
            
            if affected > 0:
                self._load_notes_list()
                self._clear_editor()
                QMessageBox.information(None, "成功", "笔记删除成功！")
    
    def _on_export_file(self):
        """
        导出文件
        """
        if not hasattr(self, '_current_note_id') or self._current_note_id is None:
            QMessageBox.warning(None, "警告", "请先选择一个笔记！")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            None, "导出文件", "",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_editor.toPlainText())
                
                QMessageBox.information(None, "成功", "文件导出成功！")
            except Exception as e:
                QMessageBox.critical(None, "错误", f"导出文件失败: {e}")
    
    def _on_import_file(self):
        """
        导入文件
        """
        file_path, _ = QFileDialog.getOpenFileName(
            None, "导入文件", "",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.text_editor.setPlainText(content)
                QMessageBox.information(None, "成功", "文件导入成功！")
            except Exception as e:
                QMessageBox.critical(None, "错误", f"导入文件失败: {e}")
