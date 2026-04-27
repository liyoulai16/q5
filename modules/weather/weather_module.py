#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气查询模块
生活工具分类下的天气查询功能
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QGroupBox, QGridLayout,
                             QScrollArea, QFrame, QMessageBox, QTabWidget, QDateEdit,
                             QSplitter, QSizePolicy)
from PyQt6.QtCore import Qt, QDate, QSize, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QLinearGradient, QPainter, QPen

from modules.module_manager import BaseModule, ModuleCategory
from database.database_manager import DatabaseManager

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class WeatherDataGenerator:
    """天气数据生成器（模拟数据）"""
    
    WEATHER_CONDITIONS = [
        ("晴", "☀️", 0.3),
        ("多云", "⛅", 0.25),
        ("阴", "☁️", 0.15),
        ("小雨", "🌧️", 0.15),
        ("中雨", "🌧️", 0.08),
        ("雷阵雨", "⛈️", 0.05),
        ("小雪", "❄️", 0.02),
    ]
    
    @classmethod
    def generate_weather(cls, city_name: str, date: datetime) -> Dict[str, Any]:
        """生成模拟天气数据"""
        random.seed(hash(city_name + date.strftime("%Y-%m-%d")) % 1000000)
        
        month = date.month
        if month in [12, 1, 2]:
            base_temp = random.randint(-5, 10)
        elif month in [3, 4, 5]:
            base_temp = random.randint(10, 25)
        elif month in [6, 7, 8]:
            base_temp = random.randint(25, 38)
        else:
            base_temp = random.randint(10, 20)
        
        temp_high = base_temp + random.randint(0, 8)
        temp_low = base_temp - random.randint(3, 8)
        
        r = random.random()
        cumulative = 0
        condition = "晴"
        icon = "☀️"
        for cond, ic, prob in cls.WEATHER_CONDITIONS:
            cumulative += prob
            if r <= cumulative:
                condition = cond
                icon = ic
                break
        
        humidity = random.randint(30, 90)
        wind_speed = random.randint(1, 30)
        wind_directions = ["东北风", "东风", "东南风", "南风", "西南风", "西风", "西北风", "北风"]
        wind_direction = random.choice(wind_directions)
        
        return {
            "city": city_name,
            "date": date.strftime("%Y-%m-%d"),
            "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()],
            "condition": condition,
            "icon": icon,
            "temp_high": temp_high,
            "temp_low": temp_low,
            "temp_current": (temp_high + temp_low) // 2 + random.randint(-2, 2),
            "humidity": humidity,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "visibility": random.randint(5, 30),
            "pressure": random.randint(980, 1040),
            "uv_index": random.randint(0, 11) if "晴" in condition or "多云" in condition else random.randint(0, 3),
            "aqi": random.randint(20, 150),
        }
    
    @classmethod
    def generate_forecast(cls, city_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """生成未来天气预报"""
        forecast = []
        today = datetime.now()
        for i in range(days):
            date = today + timedelta(days=i)
            weather = cls.generate_weather(city_name, date)
            if i == 0:
                weather["is_today"] = True
            elif i == 1:
                weather["is_tomorrow"] = True
            forecast.append(weather)
        return forecast
    
    @classmethod
    def generate_history(cls, city_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """生成历史天气数据"""
        history = []
        today = datetime.now()
        for i in range(days, 0, -1):
            date = today - timedelta(days=i)
            weather = cls.generate_weather(city_name, date)
            weather["is_history"] = True
            history.append(weather)
        return history


class WeatherIconWidget(QWidget):
    """天气图标显示组件"""
    
    def __init__(self, icon_text: str = "☀️", size: int = 80, parent=None):
        super().__init__(parent)
        self.icon_text = icon_text
        self.icon_size = size
        self.setFixedSize(size, size)
    
    def set_icon(self, icon_text: str):
        self.icon_text = icon_text
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        font = QFont("Microsoft YaHei", self.icon_size // 2)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#333333")))
        
        rect = self.rect()
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.icon_text)


class WeatherCard(QFrame):
    """天气卡片组件"""
    
    def __init__(self, weather_data: Dict[str, Any], is_today: bool = False, parent=None):
        super().__init__(parent)
        self.weather_data = weather_data
        self.is_today = is_today
        self._init_ui()
    
    def _init_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(120)
        
        if self.is_today:
            self.setStyleSheet("""
                QFrame {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #1565C0, stop:1 #1976D2);
                    border-radius: 12px;
                    border: none;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
                QFrame:hover {
                    border: 1px solid #1565C0;
                }
            """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        icon_size = 60 if self.is_today else 50
        self.icon_widget = WeatherIconWidget(self.weather_data.get("icon", "☀️"), icon_size)
        layout.addWidget(self.icon_widget)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        date_text = self.weather_data.get("weekday", "")
        if self.is_today:
            date_text = "今天 " + date_text
        elif self.weather_data.get("is_tomorrow"):
            date_text = "明天 " + date_text
        
        date_label = QLabel(date_text)
        date_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold if self.is_today else QFont.Weight.Normal))
        date_label.setStyleSheet(f"color: {'white' if self.is_today else '#333333'};")
        info_layout.addWidget(date_label)
        
        condition_label = QLabel(self.weather_data.get("condition", ""))
        condition_label.setFont(QFont("Microsoft YaHei", 11))
        condition_label.setStyleSheet(f"color: {'#E3F2FD' if self.is_today else '#666666'};")
        info_layout.addWidget(condition_label)
        
        layout.addLayout(info_layout, 1)
        
        temp_layout = QVBoxLayout()
        temp_layout.setSpacing(5)
        temp_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        temp_high = self.weather_data.get("temp_high", 0)
        temp_low = self.weather_data.get("temp_low", 0)
        
        if self.is_today:
            temp_current = self.weather_data.get("temp_current", (temp_high + temp_low) // 2)
            current_temp_label = QLabel(f"{temp_current}°C")
            current_temp_label.setFont(QFont("Microsoft YaHei", 28, QFont.Weight.Bold))
            current_temp_label.setStyleSheet("color: white;")
            current_temp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            temp_layout.addWidget(current_temp_label)
        
        temp_range_label = QLabel(f"最高 {temp_high}°C / 最低 {temp_low}°C")
        temp_range_label.setFont(QFont("Microsoft YaHei", 10))
        temp_range_label.setStyleSheet(f"color: {'#BBDEFB' if self.is_today else '#888888'};")
        temp_range_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        temp_layout.addWidget(temp_range_label)
        
        layout.addLayout(temp_layout)


class WeatherDetailWidget(QGroupBox):
    """天气详情组件"""
    
    def __init__(self, weather_data: Dict[str, Any], parent=None):
        super().__init__("天气详情", parent)
        self.weather_data = weather_data
        self._init_ui()
    
    def _init_ui(self):
        self.setStyleSheet("""
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
        
        layout = QGridLayout(self)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(15)
        
        details = [
            ("湿度", f"{self.weather_data.get('humidity', 0)}%", "💧"),
            ("风速", f"{self.weather_data.get('wind_speed', 0)} km/h", "💨"),
            ("风向", self.weather_data.get('wind_direction', ""), "🧭"),
            ("能见度", f"{self.weather_data.get('visibility', 0)} km", "👁️"),
            ("气压", f"{self.weather_data.get('pressure', 0)} hPa", "📊"),
            ("紫外线指数", str(self.weather_data.get('uv_index', 0)), "☀️"),
            ("空气质量指数", str(self.weather_data.get('aqi', 0)), "🌬️"),
        ]
        
        for i, (label, value, icon) in enumerate(details):
            row = i // 2
            col = i % 2
            
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(10)
            
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Microsoft YaHei", 16))
            item_layout.addWidget(icon_label)
            
            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)
            
            name_label = QLabel(label)
            name_label.setFont(QFont("Microsoft YaHei", 10))
            name_label.setStyleSheet("color: #666666;")
            text_layout.addWidget(name_label)
            
            value_label = QLabel(value)
            value_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
            value_label.setStyleSheet("color: #333333;")
            text_layout.addWidget(value_label)
            
            item_layout.addLayout(text_layout)
            item_layout.addStretch()
            
            layout.addWidget(item_widget, row, col)


class WeatherModuleWorker(QThread):
    """天气数据获取工作线程"""
    
    data_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, city_name: str, data_type: str = "forecast", days: int = 7):
        super().__init__()
        self.city_name = city_name
        self.data_type = data_type
        self.days = days
    
    def run(self):
        try:
            if self.data_type == "forecast":
                data = WeatherDataGenerator.generate_forecast(self.city_name, self.days)
            elif self.data_type == "history":
                data = WeatherDataGenerator.generate_history(self.city_name, self.days)
            else:
                data = []
            
            self.data_ready.emit({
                "success": True,
                "data": data,
                "city": self.city_name,
                "type": self.data_type
            })
        except Exception as e:
            self.error_occurred.emit(str(e))


class WeatherMainWidget(QWidget):
    """天气查询主界面组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_city = "北京"
        self._forecast_data = []
        self._history_data = []
        self._worker = None
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        title_label = QLabel("天气查询")
        title_label.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        city_label = QLabel("城市:")
        city_label.setFont(QFont("Microsoft YaHei", 11))
        city_label.setStyleSheet("color: #555555;")
        header_layout.addWidget(city_label)
        
        self.city_combo = QComboBox()
        self.city_combo.setEditable(True)
        self.city_combo.setMinimumWidth(150)
        self.city_combo.setFont(QFont("Microsoft YaHei", 11))
        self.city_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #1565C0;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
        """)
        
        popular_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉", "西安", "重庆"]
        self.city_combo.addItems(popular_cities)
        self.city_combo.setCurrentText("北京")
        header_layout.addWidget(self.city_combo)
        
        self.search_btn = QPushButton("查询")
        self.search_btn.setMinimumWidth(80)
        self.search_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.search_btn.clicked.connect(self._on_search)
        header_layout.addWidget(self.search_btn)
        
        main_layout.addLayout(header_layout)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Microsoft YaHei", 11))
        self.tab_widget.setStyleSheet("""
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
                padding: 10px 25px;
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
        
        self.forecast_tab = self._create_forecast_tab()
        self.tab_widget.addTab(self.forecast_tab, "📅 未来天气")
        
        self.history_tab = self._create_history_tab()
        self.tab_widget.addTab(self.history_tab, "📜 历史天气")
        
        main_layout.addWidget(self.tab_widget, 1)
        
        self._load_weather_data()
    
    def _create_forecast_tab(self) -> QWidget:
        """创建天气预报标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        self.today_card_container = QWidget()
        self.today_card_layout = QVBoxLayout(self.today_card_container)
        self.today_card_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.today_card_container)
        
        forecast_label = QLabel("未来几天预报")
        forecast_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        forecast_label.setStyleSheet("color: #333333;")
        layout.addWidget(forecast_label)
        
        self.forecast_scroll = QScrollArea()
        self.forecast_scroll.setWidgetResizable(True)
        self.forecast_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)
        
        self.forecast_container = QWidget()
        self.forecast_container_layout = QVBoxLayout(self.forecast_container)
        self.forecast_container_layout.setContentsMargins(5, 5, 5, 5)
        self.forecast_container_layout.setSpacing(10)
        
        self.forecast_scroll.setWidget(self.forecast_container)
        layout.addWidget(self.forecast_scroll, 1)
        
        return widget
    
    def _create_history_tab(self) -> QWidget:
        """创建历史天气标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        date_layout = QHBoxLayout()
        date_layout.setSpacing(10)
        
        days_label = QLabel("查询天数:")
        days_label.setFont(QFont("Microsoft YaHei", 11))
        date_layout.addWidget(days_label)
        
        self.history_days_combo = QComboBox()
        self.history_days_combo.addItems(["3天", "7天", "14天"])
        self.history_days_combo.setCurrentIndex(1)
        self.history_days_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #1565C0;
            }
        """)
        date_layout.addWidget(self.history_days_combo)
        
        date_layout.addStretch()
        
        self.refresh_history_btn = QPushButton("刷新历史数据")
        self.refresh_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.refresh_history_btn.clicked.connect(self._load_history_data)
        date_layout.addWidget(self.refresh_history_btn)
        
        layout.addLayout(date_layout)
        
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 5px;
                min-height: 20px;
            }
        """)
        
        self.history_container = QWidget()
        self.history_container_layout = QVBoxLayout(self.history_container)
        self.history_container_layout.setContentsMargins(5, 5, 5, 5)
        self.history_container_layout.setSpacing(10)
        
        self.history_scroll.setWidget(self.history_container)
        layout.addWidget(self.history_scroll, 1)
        
        return widget
    
    def _on_search(self):
        """搜索按钮点击事件"""
        city = self.city_combo.currentText().strip()
        if not city:
            QMessageBox.warning(self, "警告", "请输入城市名称！")
            return
        
        self._current_city = city
        self._load_weather_data()
    
    def _load_weather_data(self):
        """加载天气数据"""
        self.search_btn.setEnabled(False)
        self.search_btn.setText("查询中...")
        
        self._worker = WeatherModuleWorker(self._current_city, "forecast", 7)
        self._worker.data_ready.connect(self._on_forecast_data_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()
    
    def _load_history_data(self):
        """加载历史天气数据"""
        days_text = self.history_days_combo.currentText()
        days = int(days_text.replace("天", ""))
        
        self.refresh_history_btn.setEnabled(False)
        self.refresh_history_btn.setText("加载中...")
        
        self._worker = WeatherModuleWorker(self._current_city, "history", days)
        self._worker.data_ready.connect(self._on_history_data_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()
    
    def _on_forecast_data_ready(self, result: Dict[str, Any]):
        """预报数据准备完成"""
        self.search_btn.setEnabled(True)
        self.search_btn.setText("查询")
        
        if result.get("success"):
            self._forecast_data = result.get("data", [])
            self._update_forecast_display()
            self._load_history_data()
    
    def _on_history_data_ready(self, result: Dict[str, Any]):
        """历史数据准备完成"""
        self.refresh_history_btn.setEnabled(True)
        self.refresh_history_btn.setText("刷新历史数据")
        
        if result.get("success"):
            self._history_data = result.get("data", [])
            self._update_history_display()
    
    def _on_error(self, error_msg: str):
        """错误处理"""
        self.search_btn.setEnabled(True)
        self.search_btn.setText("查询")
        self.refresh_history_btn.setEnabled(True)
        self.refresh_history_btn.setText("刷新历史数据")
        
        QMessageBox.critical(self, "错误", f"获取天气数据失败: {error_msg}")
    
    def _update_forecast_display(self):
        """更新预报显示"""
        for i in reversed(range(self.today_card_layout.count())):
            self.today_card_layout.itemAt(i).widget().setParent(None)
        
        if self._forecast_data:
            today_data = self._forecast_data[0]
            today_card = WeatherCard(today_data, is_today=True)
            self.today_card_layout.addWidget(today_card)
            
            self.weather_detail = WeatherDetailWidget(today_data)
            self.today_card_layout.addWidget(self.weather_detail)
        
        for i in reversed(range(self.forecast_container_layout.count())):
            self.forecast_container_layout.itemAt(i).widget().setParent(None)
        
        for weather in self._forecast_data[1:]:
            card = WeatherCard(weather, is_today=False)
            self.forecast_container_layout.addWidget(card)
        
        self.forecast_container_layout.addStretch()
    
    def _update_history_display(self):
        """更新历史显示"""
        for i in reversed(range(self.history_container_layout.count())):
            self.history_container_layout.itemAt(i).widget().setParent(None)
        
        for weather in self._history_data:
            card = WeatherCard(weather, is_today=False)
            self.history_container_layout.addWidget(card)
        
        self.history_container_layout.addStretch()


class WeatherQueryModule(BaseModule):
    """
    天气查询模块
    提供城市天气查询功能，支持未来预报和历史天气查询
    """
    
    @property
    def module_id(self) -> str:
        return "weather_query"
    
    @property
    def name(self) -> str:
        return "天气查询"
    
    @property
    def description(self) -> str:
        return "查询城市天气，支持未来预报和历史天气记录查看"
    
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
        self._db = DatabaseManager()
        self._create_weather_history_table()
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        pass
    
    def _create_weather_history_table(self):
        """
        创建天气查询历史记录表
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS weather_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            query_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            weather_condition TEXT,
            temp_high INTEGER,
            temp_low INTEGER
        )
        """
        
        self._db.execute(create_table_sql)
    
    def _create_widget(self) -> QWidget:
        """
        创建天气查询的主界面
        """
        widget = WeatherMainWidget()
        return widget
