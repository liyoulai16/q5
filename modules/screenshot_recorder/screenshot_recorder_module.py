#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
截图录屏模块
提供屏幕截图和视频录制功能
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QSplitter, QListWidget, QListWidgetItem,
                             QGroupBox, QComboBox, QSpinBox, QCheckBox, QFileDialog,
                             QMessageBox, QTabWidget, QLineEdit, QTextEdit, QFrame,
                             QProgressBar, QSlider, QApplication)
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint, QSize, pyqtSignal, QObject, QMetaObject, Q_ARG
from PyQt6.QtGui import QFont, QPixmap, QImage, QPainter, QColor, QPen, QCursor, QGuiApplication, QScreen

from modules.module_manager import BaseModule, ModuleCategory
from database.database_manager import DatabaseManager
from PIL import Image
import io


class CaptureAreaSelector(QWidget):
    """
    区域选择器
    用于选择截图或录屏的区域
    """
    
    area_selected = pyqtSignal(QRect)
    selection_cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._start_pos = None
        self._current_pos = None
        self._is_selecting = False
        self._selected_rect = None
        self._original_pixmap = None
        self._screen_geometry = None
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool)
        
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)
        
        screen = QGuiApplication.primaryScreen()
        if screen:
            self._screen_geometry = screen.geometry()
            self.setGeometry(self._screen_geometry)
            
            self._original_pixmap = screen.grabWindow(0)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._original_pixmap and not self._original_pixmap.isNull():
            painter.drawPixmap(self.rect(), self._original_pixmap)
        
        overlay_color = QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), overlay_color)
        
        if self._start_pos and self._current_pos:
            selection_rect = QRect(self._start_pos, self._current_pos).normalized()
            
            if self._original_pixmap and not self._original_pixmap.isNull():
                source_rect = QRect(
                    selection_rect.x(),
                    selection_rect.y(),
                    selection_rect.width(),
                    selection_rect.height()
                )
                painter.drawPixmap(selection_rect, self._original_pixmap, source_rect)
            
            pen = QPen(QColor(255, 100, 100), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(selection_rect)
            
            size_text = f"{selection_rect.width()} x {selection_rect.height()}"
            
            text_width = 150
            text_height = 30
            text_x = selection_rect.x() + 5
            text_y = selection_rect.y() + 5
            
            if text_x + text_width > self.width():
                text_x = self.width() - text_width - 5
            if text_y + text_height > self.height():
                text_y = selection_rect.y() - text_height - 5
            
            text_rect = QRect(text_x, text_y, text_width, text_height)
            
            painter.fillRect(text_rect, QColor(0, 0, 0, 180))
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, size_text)
        
        instruction_text = "按住鼠标左键拖动选择区域，按 ESC 取消"
        font = QFont("Microsoft YaHei", 12, QFont.Weight.Bold)
        painter.setFont(font)
        text_rect = QRect(0, 0, self.width(), 50)
        
        painter.fillRect(text_rect, QColor(0, 0, 0, 150))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, instruction_text)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.pos()
            self._current_pos = event.pos()
            self._is_selecting = True
            self.update()
    
    def mouseMoveEvent(self, event):
        if self._is_selecting:
            self._current_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._is_selecting = False
            if self._start_pos and self._current_pos:
                self._selected_rect = QRect(self._start_pos, self._current_pos).normalized()
                if self._selected_rect.width() > 10 and self._selected_rect.height() > 10:
                    self.area_selected.emit(self._selected_rect)
            self.close()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.selection_cancelled.emit()
            self.close()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.raise_()


class ScreenshotWorker(QObject):
    """
    截图工作线程
    """
    
    finished = pyqtSignal(bool, str, str)
    progress = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self._capture_mode = "fullscreen"
        self._selected_rect = None
        self._save_path = ""
        self._file_format = "PNG"
        self._include_cursor = True
        self._delay = 0
    
    def set_params(self, capture_mode: str, selected_rect: Optional[QRect], 
                   save_path: str, file_format: str, include_cursor: bool, delay: int):
        self._capture_mode = capture_mode
        self._selected_rect = selected_rect
        self._save_path = save_path
        self._file_format = file_format
        self._include_cursor = include_cursor
        self._delay = delay
    
    def capture(self):
        try:
            if self._delay > 0:
                for i in range(self._delay, 0, -1):
                    self.progress.emit(i)
                    time.sleep(1)
            
            screen = QGuiApplication.primaryScreen()
            if not screen:
                self.finished.emit(False, "", "无法获取屏幕信息")
                return
            
            if self._capture_mode == "fullscreen":
                pixmap = screen.grabWindow(0)
            elif self._capture_mode == "area" and self._selected_rect:
                pixmap = screen.grabWindow(0, 
                    self._selected_rect.x(), 
                    self._selected_rect.y(),
                    self._selected_rect.width(),
                    self._selected_rect.height())
            elif self._capture_mode == "window":
                pixmap = screen.grabWindow(0)
            else:
                pixmap = screen.grabWindow(0)
            
            if not self._save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
                os.makedirs(default_dir, exist_ok=True)
                self._save_path = os.path.join(default_dir, f"screenshot_{timestamp}.{self._file_format.lower()}")
            
            image = pixmap.toImage()
            
            if self._file_format.upper() == "PNG":
                image.save(self._save_path, "PNG")
            elif self._file_format.upper() == "JPG" or self._file_format.upper() == "JPEG":
                image.save(self._save_path, "JPEG", 90)
            elif self._file_format.upper() == "BMP":
                image.save(self._save_path, "BMP")
            else:
                image.save(self._save_path, "PNG")
            
            self.finished.emit(True, self._save_path, "截图成功")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, "", f"截图失败: {str(e)}")


class RecorderWorker(QObject):
    """
    录屏工作线程
    """
    
    finished = pyqtSignal(bool, str, str)
    progress = pyqtSignal(int, int)
    frame_captured = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self._is_recording = False
        self._capture_mode = "fullscreen"
        self._selected_rect = None
        self._save_path = ""
        self._fps = 15
        self._duration = 0
        self._frame_count = 0
    
    def set_params(self, capture_mode: str, selected_rect: Optional[QRect],
                   save_path: str, fps: int, duration: int):
        self._capture_mode = capture_mode
        self._selected_rect = selected_rect
        self._save_path = save_path
        self._fps = fps
        self._duration = duration
    
    def start_recording(self):
        self._is_recording = True
        self._frame_count = 0
        
        try:
            screen = QGuiApplication.primaryScreen()
            if not screen:
                self.finished.emit(False, "", "无法获取屏幕信息")
                return
            
            if not self._save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_dir = os.path.join(os.path.expanduser("~"), "Videos", "Recordings")
                os.makedirs(default_dir, exist_ok=True)
                self._save_path = os.path.join(default_dir, f"recording_{timestamp}.gif")
            
            frames = []
            frame_interval = 1.0 / self._fps
            
            start_time = time.time()
            frame_idx = 0
            
            while self._is_recording:
                capture_start = time.time()
                
                if self._capture_mode == "fullscreen":
                    pixmap = screen.grabWindow(0)
                elif self._capture_mode == "area" and self._selected_rect:
                    pixmap = screen.grabWindow(0,
                        self._selected_rect.x(),
                        self._selected_rect.y(),
                        self._selected_rect.width(),
                        self._selected_rect.height())
                else:
                    pixmap = screen.grabWindow(0)
                
                image = pixmap.toImage()
                image = image.convertToFormat(QImage.Format.Format_RGB888)
                
                width = image.width()
                height = image.height()
                
                ptr = image.bits()
                ptr.setsize(image.sizeInBytes())
                arr = bytes(ptr)
                
                pil_image = Image.frombytes('RGB', (width, height), arr, 'raw', 'RGB')
                frames.append(pil_image)
                
                frame_idx += 1
                self._frame_count = frame_idx
                
                elapsed = time.time() - start_time
                self.progress.emit(frame_idx, int(elapsed))
                self.frame_captured.emit(frame_idx)
                
                if self._duration > 0 and elapsed >= self._duration:
                    break
                
                elapsed_capture = time.time() - capture_start
                sleep_time = max(0, frame_interval - elapsed_capture)
                time.sleep(sleep_time)
            
            if frames:
                first_frame = frames[0]
                other_frames = frames[1:] if len(frames) > 1 else []
                
                first_frame.save(
                    self._save_path,
                    save_all=True,
                    append_images=other_frames,
                    duration=int(1000 / self._fps),
                    loop=0
                )
                
                self.finished.emit(True, self._save_path, f"录制完成，共 {len(frames)} 帧")
            else:
                self.finished.emit(False, "", "没有捕获到任何帧")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, "", f"录制失败: {str(e)}")
    
    def stop_recording(self):
        self._is_recording = False


class ScreenshotRecorderModule(BaseModule):
    """
    截图录屏模块
    提供屏幕截图和视频录制功能
    """
    
    @property
    def module_id(self) -> str:
        return "screenshot_recorder"
    
    @property
    def name(self) -> str:
        return "截图录屏"
    
    @property
    def description(self) -> str:
        return "提供屏幕截图和视频录制功能，支持全屏、区域和窗口模式"
    
    @property
    def version(self) -> str:
        return "1.0.1"
    
    @property
    def category(self) -> str:
        return ModuleCategory.OFFICE_TOOLS
    
    @property
    def author(self) -> str:
        return "System"
    
    def _on_load(self) -> None:
        """
        模块加载时的初始化
        """
        self._db = DatabaseManager()
        self._create_screenshot_table()
        self._create_recording_table()
        self._load_settings()
        
        self._screenshot_worker = ScreenshotWorker()
        self._recorder_worker = RecorderWorker()
        
        self._screenshot_worker.finished.connect(self._on_screenshot_finished)
        self._screenshot_worker.progress.connect(self._on_screenshot_progress)
        
        self._recorder_worker.finished.connect(self._on_recording_finished)
        self._recorder_worker.progress.connect(self._on_recording_progress)
        self._recorder_worker.frame_captured.connect(self._on_frame_captured)
        
        self._is_recording = False
        self._recording_timer = QTimer()
        self._recording_timer.timeout.connect(self._update_recording_timer)
        self._recording_start_time = None
        self._selected_capture_rect = None
        self._area_selector = None
        self._screenshot_in_progress = False
        self._recording_thread = None
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        if self._is_recording:
            self._stop_recording_internal()
    
    def _create_screenshot_table(self):
        """
        创建截图历史记录表
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS screenshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            width INTEGER DEFAULT 0,
            height INTEGER DEFAULT 0,
            capture_mode TEXT DEFAULT 'fullscreen',
            file_format TEXT DEFAULT 'PNG',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self._db.execute(create_table_sql)
        
        create_index_sql = "CREATE INDEX IF NOT EXISTS idx_screenshots_created_at ON screenshots(created_at)"
        self._db.execute(create_index_sql)
    
    def _create_recording_table(self):
        """
        创建录屏历史记录表
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            width INTEGER DEFAULT 0,
            height INTEGER DEFAULT 0,
            duration INTEGER DEFAULT 0,
            fps INTEGER DEFAULT 15,
            capture_mode TEXT DEFAULT 'fullscreen',
            file_format TEXT DEFAULT 'GIF',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self._db.execute(create_table_sql)
        
        create_index_sql = "CREATE INDEX IF NOT EXISTS idx_recordings_created_at ON recordings(created_at)"
        self._db.execute(create_index_sql)
    
    def _load_settings(self):
        """
        加载模块设置
        """
        self._screenshot_save_dir = self._db.get_setting(
            "screenshot_save_dir", 
            os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots"),
            self.module_id
        )
        self._recording_save_dir = self._db.get_setting(
            "recording_save_dir",
            os.path.join(os.path.expanduser("~"), "Videos", "Recordings"),
            self.module_id
        )
        self._default_image_format = self._db.get_setting(
            "default_image_format", "PNG", self.module_id
        )
        self._default_video_format = self._db.get_setting(
            "default_video_format", "GIF", self.module_id
        )
        self._default_fps = int(self._db.get_setting(
            "default_fps", "15", self.module_id
        ))
    
    def _save_settings(self):
        """
        保存模块设置
        """
        self._db.set_setting("screenshot_save_dir", self._screenshot_save_dir, self.module_id)
        self._db.set_setting("recording_save_dir", self._recording_save_dir, self.module_id)
        self._db.set_setting("default_image_format", self._default_image_format, self.module_id)
        self._db.set_setting("default_video_format", self._default_video_format, self.module_id)
        self._db.set_setting("default_fps", str(self._default_fps), self.module_id)
    
    def _create_widget(self) -> QWidget:
        """
        创建截图录屏模块的主界面
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
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)
        
        screenshot_tab = self._create_screenshot_tab()
        recording_tab = self._create_recording_tab()
        history_tab = self._create_history_tab()
        settings_tab = self._create_settings_tab()
        
        self._tab_widget.addTab(screenshot_tab, "📸 截图")
        self._tab_widget.addTab(recording_tab, "🎥 录屏")
        self._tab_widget.addTab(history_tab, "📁 历史记录")
        self._tab_widget.addTab(settings_tab, "⚙️ 设置")
        
        main_layout.addWidget(self._tab_widget, 1)
        
        return widget
    
    def _create_screenshot_tab(self) -> QWidget:
        """
        创建截图选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        settings_group = QGroupBox("截图设置")
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
        
        mode_row = QHBoxLayout()
        mode_label = QLabel("截图模式:")
        mode_label.setFont(QFont("Microsoft YaHei", 10))
        mode_row.addWidget(mode_label)
        
        self._screenshot_mode_combo = QComboBox()
        self._screenshot_mode_combo.addItems(["全屏截图", "区域截图", "窗口截图"])
        self._screenshot_mode_combo.setFont(QFont("Microsoft YaHei", 10))
        self._screenshot_mode_combo.setMinimumWidth(150)
        mode_row.addWidget(self._screenshot_mode_combo)
        mode_row.addStretch()
        settings_layout.addLayout(mode_row)
        
        format_row = QHBoxLayout()
        format_label = QLabel("图片格式:")
        format_label.setFont(QFont("Microsoft YaHei", 10))
        format_row.addWidget(format_label)
        
        self._image_format_combo = QComboBox()
        self._image_format_combo.addItems(["PNG", "JPG", "BMP"])
        self._image_format_combo.setCurrentText(self._default_image_format)
        self._image_format_combo.setFont(QFont("Microsoft YaHei", 10))
        self._image_format_combo.setMinimumWidth(100)
        format_row.addWidget(self._image_format_combo)
        format_row.addStretch()
        settings_layout.addLayout(format_row)
        
        delay_row = QHBoxLayout()
        delay_label = QLabel("延迟截图(秒):")
        delay_label.setFont(QFont("Microsoft YaHei", 10))
        delay_row.addWidget(delay_label)
        
        self._delay_spin = QSpinBox()
        self._delay_spin.setRange(0, 10)
        self._delay_spin.setValue(0)
        self._delay_spin.setFont(QFont("Microsoft YaHei", 10))
        self._delay_spin.setMinimumWidth(80)
        delay_row.addWidget(self._delay_spin)
        delay_row.addStretch()
        settings_layout.addLayout(delay_row)
        
        cursor_row = QHBoxLayout()
        self._include_cursor_check = QCheckBox("包含鼠标光标")
        self._include_cursor_check.setFont(QFont("Microsoft YaHei", 10))
        self._include_cursor_check.setChecked(True)
        cursor_row.addWidget(self._include_cursor_check)
        cursor_row.addStretch()
        settings_layout.addLayout(cursor_row)
        
        layout.addWidget(settings_group)
        
        action_group = QGroupBox("操作")
        action_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        action_group.setStyleSheet("""
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
        action_layout = QHBoxLayout(action_group)
        action_layout.setSpacing(10)
        
        self._capture_btn = QPushButton("📷 立即截图")
        self._capture_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._capture_btn.setMinimumHeight(45)
        self._capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self._capture_btn.clicked.connect(self._on_capture_screenshot)
        action_layout.addWidget(self._capture_btn)
        
        self._select_area_btn = QPushButton("🔲 选择区域")
        self._select_area_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._select_area_btn.setMinimumHeight(45)
        self._select_area_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self._select_area_btn.clicked.connect(self._on_select_area)
        action_layout.addWidget(self._select_area_btn)
        
        self._preview_label = QLabel("所选区域: 未选择")
        self._preview_label.setFont(QFont("Microsoft YaHei", 10))
        self._preview_label.setStyleSheet("color: #666;")
        action_layout.addWidget(self._preview_label)
        
        action_layout.addStretch()
        layout.addWidget(action_group)
        
        self._screenshot_status_label = QLabel("就绪")
        self._screenshot_status_label.setFont(QFont("Microsoft YaHei", 10))
        self._screenshot_status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self._screenshot_status_label)
        
        layout.addStretch()
        
        return tab
    
    def _create_recording_tab(self) -> QWidget:
        """
        创建录屏选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        settings_group = QGroupBox("录屏设置")
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
        
        mode_row = QHBoxLayout()
        mode_label = QLabel("录制模式:")
        mode_label.setFont(QFont("Microsoft YaHei", 10))
        mode_row.addWidget(mode_label)
        
        self._recording_mode_combo = QComboBox()
        self._recording_mode_combo.addItems(["全屏录制", "区域录制"])
        self._recording_mode_combo.setFont(QFont("Microsoft YaHei", 10))
        self._recording_mode_combo.setMinimumWidth(150)
        mode_row.addWidget(self._recording_mode_combo)
        mode_row.addStretch()
        settings_layout.addLayout(mode_row)
        
        fps_row = QHBoxLayout()
        fps_label = QLabel("帧率(FPS):")
        fps_label.setFont(QFont("Microsoft YaHei", 10))
        fps_row.addWidget(fps_label)
        
        self._fps_combo = QComboBox()
        self._fps_combo.addItems(["10", "15", "20", "25", "30"])
        self._fps_combo.setCurrentText(str(self._default_fps))
        self._fps_combo.setFont(QFont("Microsoft YaHei", 10))
        self._fps_combo.setMinimumWidth(100)
        fps_row.addWidget(self._fps_combo)
        fps_row.addStretch()
        settings_layout.addLayout(fps_row)
        
        duration_row = QHBoxLayout()
        duration_label = QLabel("录制时长(秒, 0为无限):")
        duration_label.setFont(QFont("Microsoft YaHei", 10))
        duration_row.addWidget(duration_label)
        
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(0, 3600)
        self._duration_spin.setValue(0)
        self._duration_spin.setFont(QFont("Microsoft YaHei", 10))
        self._duration_spin.setMinimumWidth(80)
        duration_row.addWidget(self._duration_spin)
        duration_row.addStretch()
        settings_layout.addLayout(duration_row)
        
        layout.addWidget(settings_group)
        
        action_group = QGroupBox("录制控制")
        action_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        action_group.setStyleSheet("""
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
        action_layout = QHBoxLayout(action_group)
        action_layout.setSpacing(10)
        
        self._start_recording_btn = QPushButton("▶️ 开始录制")
        self._start_recording_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._start_recording_btn.setMinimumHeight(45)
        self._start_recording_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self._start_recording_btn.clicked.connect(self._on_start_recording)
        action_layout.addWidget(self._start_recording_btn)
        
        self._stop_recording_btn = QPushButton("⏹️ 停止录制")
        self._stop_recording_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._stop_recording_btn.setMinimumHeight(45)
        self._stop_recording_btn.setEnabled(False)
        self._stop_recording_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
            }
            QPushButton:enabled:hover {
                background-color: #757575;
            }
        """)
        self._stop_recording_btn.clicked.connect(self._on_stop_recording)
        action_layout.addWidget(self._stop_recording_btn)
        
        self._select_recording_area_btn = QPushButton("🔲 选择区域")
        self._select_recording_area_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._select_recording_area_btn.setMinimumHeight(45)
        self._select_recording_area_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self._select_recording_area_btn.clicked.connect(self._on_select_recording_area)
        action_layout.addWidget(self._select_recording_area_btn)
        
        action_layout.addStretch()
        layout.addWidget(action_group)
        
        status_group = QGroupBox("录制状态")
        status_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        status_group.setStyleSheet("""
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
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(10)
        
        self._recording_timer_label = QLabel("录制时间: 00:00:00")
        self._recording_timer_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        self._recording_timer_label.setStyleSheet("color: #333;")
        self._recording_timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self._recording_timer_label)
        
        self._recording_frames_label = QLabel("已捕获帧: 0")
        self._recording_frames_label.setFont(QFont("Microsoft YaHei", 11))
        self._recording_frames_label.setStyleSheet("color: #666;")
        self._recording_frames_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self._recording_frames_label)
        
        self._recording_status_label = QLabel("就绪")
        self._recording_status_label.setFont(QFont("Microsoft YaHei", 10))
        self._recording_status_label.setStyleSheet("color: #666; padding: 5px;")
        self._recording_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self._recording_status_label)
        
        layout.addWidget(status_group)
        layout.addStretch()
        
        return tab
    
    def _create_history_tab(self) -> QWidget:
        """
        创建历史记录选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        search_row = QHBoxLayout()
        search_label = QLabel("搜索:")
        search_label.setFont(QFont("Microsoft YaHei", 10))
        search_row.addWidget(search_label)
        
        self._history_search_edit = QLineEdit()
        self._history_search_edit.setPlaceholderText("输入文件名或日期搜索...")
        self._history_search_edit.setFont(QFont("Microsoft YaHei", 10))
        self._history_search_edit.setMinimumWidth(300)
        self._history_search_edit.textChanged.connect(self._on_search_history)
        search_row.addWidget(self._history_search_edit)
        
        self._history_type_combo = QComboBox()
        self._history_type_combo.addItems(["全部", "截图", "录屏"])
        self._history_type_combo.setFont(QFont("Microsoft YaHei", 10))
        self._history_type_combo.currentTextChanged.connect(self._on_filter_history)
        search_row.addWidget(self._history_type_combo)
        
        self._refresh_history_btn = QPushButton("🔄 刷新")
        self._refresh_history_btn.setFont(QFont("Microsoft YaHei", 10))
        self._refresh_history_btn.clicked.connect(self._refresh_history_list)
        search_row.addWidget(self._refresh_history_btn)
        
        search_row.addStretch()
        layout.addLayout(search_row)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(5)
        
        list_title = QLabel("文件列表")
        list_title.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        list_title.setStyleSheet("color: #333;")
        list_layout.addWidget(list_title)
        
        self._history_list = QListWidget()
        self._history_list.setFont(QFont("Microsoft YaHei", 10))
        self._history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
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
        self._history_list.currentRowChanged.connect(self._on_history_item_selected)
        list_layout.addWidget(self._history_list, 1)
        
        splitter.addWidget(list_panel)
        
        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(5)
        
        detail_title = QLabel("详细信息")
        detail_title.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        detail_title.setStyleSheet("color: #333;")
        detail_layout.addWidget(detail_title)
        
        self._history_detail_text = QTextEdit()
        self._history_detail_text.setFont(QFont("Microsoft YaHei", 10))
        self._history_detail_text.setReadOnly(True)
        self._history_detail_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                background-color: #fafafa;
            }
        """)
        detail_layout.addWidget(self._history_detail_text, 1)
        
        action_row = QHBoxLayout()
        
        self._open_file_btn = QPushButton("📂 打开文件")
        self._open_file_btn.setFont(QFont("Microsoft YaHei", 10))
        self._open_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self._open_file_btn.clicked.connect(self._on_open_file)
        action_row.addWidget(self._open_file_btn)
        
        self._open_folder_btn = QPushButton("📁 打开文件夹")
        self._open_folder_btn.setFont(QFont("Microsoft YaHei", 10))
        self._open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self._open_folder_btn.clicked.connect(self._on_open_folder)
        action_row.addWidget(self._open_folder_btn)
        
        self._delete_history_btn = QPushButton("🗑️ 删除记录")
        self._delete_history_btn.setFont(QFont("Microsoft YaHei", 10))
        self._delete_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self._delete_history_btn.clicked.connect(self._on_delete_history)
        action_row.addWidget(self._delete_history_btn)
        
        action_row.addStretch()
        detail_layout.addLayout(action_row)
        
        splitter.addWidget(detail_panel)
        splitter.setSizes([400, 400])
        
        layout.addWidget(splitter, 1)
        
        self._refresh_history_list()
        
        return tab
    
    def _create_settings_tab(self) -> QWidget:
        """
        创建设置选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        screenshot_group = QGroupBox("截图设置")
        screenshot_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        screenshot_group.setStyleSheet("""
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
        screenshot_layout = QVBoxLayout(screenshot_group)
        screenshot_layout.setSpacing(10)
        
        screenshot_dir_row = QHBoxLayout()
        screenshot_dir_label = QLabel("截图保存目录:")
        screenshot_dir_label.setFont(QFont("Microsoft YaHei", 10))
        screenshot_dir_row.addWidget(screenshot_dir_label)
        
        self._screenshot_dir_edit = QLineEdit()
        self._screenshot_dir_edit.setText(self._screenshot_save_dir)
        self._screenshot_dir_edit.setFont(QFont("Microsoft YaHei", 10))
        self._screenshot_dir_edit.setMinimumWidth(300)
        screenshot_dir_row.addWidget(self._screenshot_dir_edit)
        
        self._browse_screenshot_dir_btn = QPushButton("浏览...")
        self._browse_screenshot_dir_btn.setFont(QFont("Microsoft YaHei", 10))
        self._browse_screenshot_dir_btn.clicked.connect(self._on_browse_screenshot_dir)
        screenshot_dir_row.addWidget(self._browse_screenshot_dir_btn)
        
        screenshot_dir_row.addStretch()
        screenshot_layout.addLayout(screenshot_dir_row)
        
        layout.addWidget(screenshot_group)
        
        recording_group = QGroupBox("录屏设置")
        recording_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        recording_group.setStyleSheet("""
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
        recording_layout = QVBoxLayout(recording_group)
        recording_layout.setSpacing(10)
        
        recording_dir_row = QHBoxLayout()
        recording_dir_label = QLabel("录屏保存目录:")
        recording_dir_label.setFont(QFont("Microsoft YaHei", 10))
        recording_dir_row.addWidget(recording_dir_label)
        
        self._recording_dir_edit = QLineEdit()
        self._recording_dir_edit.setText(self._recording_save_dir)
        self._recording_dir_edit.setFont(QFont("Microsoft YaHei", 10))
        self._recording_dir_edit.setMinimumWidth(300)
        recording_dir_row.addWidget(self._recording_dir_edit)
        
        self._browse_recording_dir_btn = QPushButton("浏览...")
        self._browse_recording_dir_btn.setFont(QFont("Microsoft YaHei", 10))
        self._browse_recording_dir_btn.clicked.connect(self._on_browse_recording_dir)
        recording_dir_row.addWidget(self._browse_recording_dir_btn)
        
        recording_dir_row.addStretch()
        recording_layout.addLayout(recording_dir_row)
        
        layout.addWidget(recording_group)
        
        default_group = QGroupBox("默认设置")
        default_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        default_group.setStyleSheet("""
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
        default_layout = QVBoxLayout(default_group)
        default_layout.setSpacing(10)
        
        default_image_row = QHBoxLayout()
        default_image_label = QLabel("默认图片格式:")
        default_image_label.setFont(QFont("Microsoft YaHei", 10))
        default_image_row.addWidget(default_image_label)
        
        self._default_image_combo = QComboBox()
        self._default_image_combo.addItems(["PNG", "JPG", "BMP"])
        self._default_image_combo.setCurrentText(self._default_image_format)
        self._default_image_combo.setFont(QFont("Microsoft YaHei", 10))
        default_image_row.addWidget(self._default_image_combo)
        default_image_row.addStretch()
        default_layout.addLayout(default_image_row)
        
        default_fps_row = QHBoxLayout()
        default_fps_label = QLabel("默认帧率(FPS):")
        default_fps_label.setFont(QFont("Microsoft YaHei", 10))
        default_fps_row.addWidget(default_fps_label)
        
        self._default_fps_combo = QComboBox()
        self._default_fps_combo.addItems(["10", "15", "20", "25", "30"])
        self._default_fps_combo.setCurrentText(str(self._default_fps))
        self._default_fps_combo.setFont(QFont("Microsoft YaHei", 10))
        default_fps_row.addWidget(self._default_fps_combo)
        default_fps_row.addStretch()
        default_layout.addLayout(default_fps_row)
        
        layout.addWidget(default_group)
        
        save_row = QHBoxLayout()
        self._save_settings_btn = QPushButton("💾 保存设置")
        self._save_settings_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._save_settings_btn.setMinimumHeight(45)
        self._save_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self._save_settings_btn.clicked.connect(self._on_save_settings)
        save_row.addWidget(self._save_settings_btn)
        save_row.addStretch()
        layout.addLayout(save_row)
        
        layout.addStretch()
        
        return tab
    
    def _on_capture_screenshot(self):
        """
        执行截图
        """
        if self._screenshot_in_progress:
            QMessageBox.warning(None, "警告", "截图操作正在进行中，请稍候...")
            return
        
        mode_text = self._screenshot_mode_combo.currentText()
        if mode_text == "全屏截图":
            capture_mode = "fullscreen"
        elif mode_text == "区域截图":
            capture_mode = "area"
            if not self._selected_capture_rect:
                QMessageBox.warning(None, "警告", "请先选择截图区域！")
                return
        else:
            capture_mode = "window"
        
        file_format = self._image_format_combo.currentText()
        delay = self._delay_spin.value()
        include_cursor = self._include_cursor_check.isChecked()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(self._screenshot_save_dir, exist_ok=True)
        save_path = os.path.join(self._screenshot_save_dir, f"screenshot_{timestamp}.{file_format.lower()}")
        
        self._screenshot_worker.set_params(
            capture_mode,
            self._selected_capture_rect,
            save_path,
            file_format,
            include_cursor,
            delay
        )
        
        self._screenshot_in_progress = True
        self._screenshot_status_label.setText(f"正在截图... (延迟 {delay} 秒)" if delay > 0 else "正在截图...")
        self._capture_btn.setEnabled(False)
        
        screenshot_thread = threading.Thread(target=self._screenshot_worker.capture)
        screenshot_thread.daemon = True
        screenshot_thread.start()
    
    def _on_screenshot_progress(self, remaining):
        self._screenshot_status_label.setText(f"截图倒计时: {remaining} 秒...")
    
    def _on_screenshot_finished(self, success: bool, file_path: str, message: str):
        self._screenshot_in_progress = False
        self._capture_btn.setEnabled(True)
        
        if success:
            try:
                file_size = os.path.getsize(file_path)
                filename = os.path.basename(file_path)
                
                image = QImage(file_path)
                width = image.width()
                height = image.height()
                
                self._db.insert('screenshots', {
                    'filename': filename,
                    'file_path': file_path,
                    'file_size': file_size,
                    'width': width,
                    'height': height,
                    'capture_mode': self._screenshot_mode_combo.currentText(),
                    'file_format': self._image_format_combo.currentText()
                })
                
                self._screenshot_status_label.setText(f"截图成功: {filename} ({self._format_file_size(file_size)})")
                QMessageBox.information(None, "成功", f"截图已保存到:\n{file_path}")
                
                self._refresh_history_list()
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._screenshot_status_label.setText(f"保存记录失败: {str(e)}")
        else:
            self._screenshot_status_label.setText(message)
            QMessageBox.critical(None, "错误", message)
    
    def _on_select_area(self):
        """
        选择截图区域
        """
        if self._area_selector:
            try:
                self._area_selector.close()
            except:
                pass
        
        self._area_selector = CaptureAreaSelector()
        self._area_selector.area_selected.connect(self._on_area_selected)
        self._area_selector.selection_cancelled.connect(self._on_area_selection_cancelled)
        self._area_selector.showFullScreen()
        self._area_selector.activateWindow()
        self._area_selector.raise_()
    
    def _on_area_selected(self, rect: QRect):
        print(f"选择的区域: x={rect.x()}, y={rect.y()}, width={rect.width()}, height={rect.height()}")
        self._selected_capture_rect = QRect(rect)
        self._preview_label.setText(f"所选区域: {rect.width()} x {rect.height()}")
        self._preview_label.setStyleSheet("color: #4CAF50;")
    
    def _on_area_selection_cancelled(self):
        self._preview_label.setText("所选区域: 未选择")
        self._preview_label.setStyleSheet("color: #666;")
    
    def _on_select_recording_area(self):
        """
        选择录屏区域
        """
        if self._area_selector:
            try:
                self._area_selector.close()
            except:
                pass
        
        self._area_selector = CaptureAreaSelector()
        self._area_selector.area_selected.connect(self._on_recording_area_selected)
        self._area_selector.selection_cancelled.connect(self._on_recording_area_cancelled)
        self._area_selector.showFullScreen()
        self._area_selector.activateWindow()
        self._area_selector.raise_()
    
    def _on_recording_area_selected(self, rect: QRect):
        print(f"选择的录制区域: x={rect.x()}, y={rect.y()}, width={rect.width()}, height={rect.height()}")
        self._selected_capture_rect = QRect(rect)
    
    def _on_recording_area_cancelled(self):
        pass
    
    def _on_start_recording(self):
        """
        开始录制
        """
        if self._is_recording:
            QMessageBox.warning(None, "警告", "录制正在进行中...")
            return
        
        mode_text = self._recording_mode_combo.currentText()
        if mode_text == "全屏录制":
            capture_mode = "fullscreen"
        else:
            capture_mode = "area"
            if not self._selected_capture_rect:
                QMessageBox.warning(None, "警告", "请先选择录制区域！")
                return
        
        fps = int(self._fps_combo.currentText())
        duration = self._duration_spin.value()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(self._recording_save_dir, exist_ok=True)
        save_path = os.path.join(self._recording_save_dir, f"recording_{timestamp}.gif")
        
        self._recorder_worker.set_params(
            capture_mode,
            self._selected_capture_rect,
            save_path,
            fps,
            duration
        )
        
        self._is_recording = True
        self._recording_start_time = time.time()
        self._recording_timer.start(1000)
        
        self._start_recording_btn.setEnabled(False)
        self._stop_recording_btn.setEnabled(True)
        self._recording_status_label.setText("正在录制...")
        self._recording_status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        
        self._recording_thread = threading.Thread(target=self._recorder_worker.start_recording)
        self._recording_thread.daemon = True
        self._recording_thread.start()
    
    def _on_stop_recording(self):
        """
        停止录制
        """
        self._stop_recording_internal()
    
    def _stop_recording_internal(self):
        """
        内部停止录制方法
        """
        if self._is_recording:
            self._recorder_worker.stop_recording()
            self._recording_timer.stop()
            self._is_recording = False
            
            self._start_recording_btn.setEnabled(True)
            self._stop_recording_btn.setEnabled(False)
            self._recording_status_label.setText("正在处理视频...")
            self._recording_status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
    
    def _update_recording_timer(self):
        """
        更新录制计时器
        """
        if self._recording_start_time:
            elapsed = int(time.time() - self._recording_start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self._recording_timer_label.setText(f"录制时间: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def _on_recording_progress(self, frame_count: int, elapsed: int):
        pass
    
    def _on_frame_captured(self, frame_count: int):
        self._recording_frames_label.setText(f"已捕获帧: {frame_count}")
    
    def _on_recording_finished(self, success: bool, file_path: str, message: str):
        self._is_recording = False
        
        self._start_recording_btn.setEnabled(True)
        self._stop_recording_btn.setEnabled(False)
        
        if success:
            try:
                file_size = os.path.getsize(file_path)
                filename = os.path.basename(file_path)
                
                duration = 0
                if self._recording_start_time:
                    duration = int(time.time() - self._recording_start_time)
                
                width = 0
                height = 0
                if self._selected_capture_rect:
                    width = self._selected_capture_rect.width()
                    height = self._selected_capture_rect.height()
                
                self._db.insert('recordings', {
                    'filename': filename,
                    'file_path': file_path,
                    'file_size': file_size,
                    'width': width,
                    'height': height,
                    'duration': duration,
                    'fps': int(self._fps_combo.currentText()),
                    'capture_mode': self._recording_mode_combo.currentText(),
                    'file_format': 'GIF'
                })
                
                self._recording_status_label.setText(f"录制完成: {filename}")
                self._recording_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                QMessageBox.information(None, "成功", f"录制已保存到:\n{file_path}\n\n{message}")
                
                self._refresh_history_list()
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._recording_status_label.setText(f"保存记录失败: {str(e)}")
                self._recording_status_label.setStyleSheet("color: #f44336;")
        else:
            self._recording_status_label.setText(message)
            self._recording_status_label.setStyleSheet("color: #f44336;")
            QMessageBox.critical(None, "错误", message)
    
    def _refresh_history_list(self):
        """
        刷新历史记录列表
        """
        self._history_list.clear()
        self._history_data = []
        
        screenshots = self._db.query_all(
            "SELECT id, filename, file_path, file_size, width, height, capture_mode, file_format, created_at, 'screenshot' as type FROM screenshots ORDER BY created_at DESC"
        )
        
        recordings = self._db.query_all(
            "SELECT id, filename, file_path, file_size, width, height, duration, fps, capture_mode, file_format, created_at, 'recording' as type FROM recordings ORDER BY created_at DESC"
        )
        
        all_items = screenshots + recordings
        all_items.sort(key=lambda x: x['created_at'], reverse=True)
        
        for item in all_items:
            self._history_data.append(item)
            type_icon = "📸" if item['type'] == 'screenshot' else "🎥"
            list_item = QListWidgetItem(f"{type_icon} {item['filename']}")
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            list_item.setToolTip(f"路径: {item['file_path']}\n大小: {self._format_file_size(item['file_size'])}")
            self._history_list.addItem(list_item)
    
    def _on_search_history(self, text: str):
        """
        搜索历史记录
        """
        search_text = text.lower()
        
        for i in range(self._history_list.count()):
            item = self._history_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            
            if not search_text:
                item.setHidden(False)
            else:
                filename = data.get('filename', '').lower()
                created_at = data.get('created_at', '').lower()
                
                if search_text in filename or search_text in created_at:
                    item.setHidden(False)
                else:
                    item.setHidden(True)
    
    def _on_filter_history(self, filter_type: str):
        """
        过滤历史记录
        """
        for i in range(self._history_list.count()):
            item = self._history_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            
            if filter_type == "全部":
                item.setHidden(False)
            elif filter_type == "截图" and data.get('type') == 'screenshot':
                item.setHidden(False)
            elif filter_type == "录屏" and data.get('type') == 'recording':
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def _on_history_item_selected(self, index: int):
        """
        历史记录项选中
        """
        if index < 0:
            self._history_detail_text.clear()
            return
        
        item = self._history_list.item(index)
        if not item:
            return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        self._selected_history_item = data
        
        detail_text = ""
        if data.get('type') == 'screenshot':
            detail_text = f"""📸 截图信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

文件名: {data.get('filename', 'N/A')}
文件路径: {data.get('file_path', 'N/A')}
文件大小: {self._format_file_size(data.get('file_size', 0))}
分辨率: {data.get('width', 0)} x {data.get('height', 0)}
截图模式: {data.get('capture_mode', 'N/A')}
图片格式: {data.get('file_format', 'N/A')}
创建时间: {data.get('created_at', 'N/A')}
"""
        else:
            duration = data.get('duration', 0)
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            
            detail_text = f"""🎥 录屏信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

文件名: {data.get('filename', 'N/A')}
文件路径: {data.get('file_path', 'N/A')}
文件大小: {self._format_file_size(data.get('file_size', 0))}
分辨率: {data.get('width', 0)} x {data.get('height', 0)}
录制时长: {hours:02d}:{minutes:02d}:{seconds:02d}
帧率: {data.get('fps', 0)} FPS
录制模式: {data.get('capture_mode', 'N/A')}
视频格式: {data.get('file_format', 'N/A')}
创建时间: {data.get('created_at', 'N/A')}
"""
        
        self._history_detail_text.setText(detail_text)
    
    def _on_open_file(self):
        """
        打开文件
        """
        if not hasattr(self, '_selected_history_item') or not self._selected_history_item:
            QMessageBox.warning(None, "警告", "请先选择一个文件！")
            return
        
        file_path = self._selected_history_item.get('file_path', '')
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(None, "警告", "文件不存在！")
            return
        
        try:
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.critical(None, "错误", f"无法打开文件: {str(e)}")
    
    def _on_open_folder(self):
        """
        打开文件夹
        """
        if not hasattr(self, '_selected_history_item') or not self._selected_history_item:
            QMessageBox.warning(None, "警告", "请先选择一个文件！")
            return
        
        file_path = self._selected_history_item.get('file_path', '')
        if not file_path:
            QMessageBox.warning(None, "警告", "文件路径无效！")
            return
        
        folder_path = os.path.dirname(file_path)
        if not os.path.exists(folder_path):
            QMessageBox.warning(None, "警告", "文件夹不存在！")
            return
        
        try:
            os.startfile(folder_path)
        except Exception as e:
            QMessageBox.critical(None, "错误", f"无法打开文件夹: {str(e)}")
    
    def _on_delete_history(self):
        """
        删除历史记录
        """
        if not hasattr(self, '_selected_history_item') or not self._selected_history_item:
            QMessageBox.warning(None, "警告", "请先选择一个文件！")
            return
        
        data = self._selected_history_item
        item_type = data.get('type', '')
        item_id = data.get('id', 0)
        filename = data.get('filename', '')
        
        reply = QMessageBox.question(
            None, "确认删除",
            f"确定要删除记录 \"{filename}\" 吗？\n\n注意: 这只会删除数据库记录，不会删除实际文件。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            table = 'screenshots' if item_type == 'screenshot' else 'recordings'
            affected = self._db.delete(table, 'id = ?', (item_id,))
            
            if affected > 0:
                QMessageBox.information(None, "成功", "记录已删除！")
                self._refresh_history_list()
                self._history_detail_text.clear()
    
    def _on_browse_screenshot_dir(self):
        """
        浏览截图保存目录
        """
        dir_path = QFileDialog.getExistingDirectory(None, "选择截图保存目录", self._screenshot_dir_edit.text())
        if dir_path:
            self._screenshot_dir_edit.setText(dir_path)
    
    def _on_browse_recording_dir(self):
        """
        浏览录屏保存目录
        """
        dir_path = QFileDialog.getExistingDirectory(None, "选择录屏保存目录", self._recording_dir_edit.text())
        if dir_path:
            self._recording_dir_edit.setText(dir_path)
    
    def _on_save_settings(self):
        """
        保存设置
        """
        self._screenshot_save_dir = self._screenshot_dir_edit.text()
        self._recording_save_dir = self._recording_dir_edit.text()
        self._default_image_format = self._default_image_combo.currentText()
        self._default_fps = int(self._default_fps_combo.currentText())
        
        self._save_settings()
        
        self._image_format_combo.setCurrentText(self._default_image_format)
        self._fps_combo.setCurrentText(str(self._default_fps))
        
        QMessageBox.information(None, "成功", "设置已保存！")
    
    def _format_file_size(self, size: int) -> str:
        """
        格式化文件大小
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"