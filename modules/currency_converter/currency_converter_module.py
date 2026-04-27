#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汇率换算模块
生活工具分类下的汇率换算功能
"""

import json
import os
import urllib3
from datetime import datetime
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QGroupBox, QGridLayout,
                             QScrollArea, QFrame, QMessageBox, QTabWidget, QSpacerItem,
                             QSizePolicy, QListWidget, QListWidgetItem, QSplitter)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QColor, QLinearGradient, QPainter, QPen, QPixmap

from modules.module_manager import BaseModule, ModuleCategory
from database.database_manager import DatabaseManager

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NO_PROXY_ENV = {
    'http_proxy': '',
    'https_proxy': '',
    'HTTP_PROXY': '',
    'HTTPS_PROXY': '',
    'no_proxy': '*',
    'NO_PROXY': '*',
}

CURRENCIES = {
    "CNY": {"name": "人民币", "symbol": "¥", "flag": "🇨🇳"},
    "USD": {"name": "美元", "symbol": "$", "flag": "🇺🇸"},
    "EUR": {"name": "欧元", "symbol": "€", "flag": "🇪🇺"},
    "GBP": {"name": "英镑", "symbol": "£", "flag": "🇬🇧"},
    "JPY": {"name": "日元", "symbol": "¥", "flag": "🇯🇵"},
    "AUD": {"name": "澳元", "symbol": "A$", "flag": "🇦🇺"},
    "CAD": {"name": "加元", "symbol": "C$", "flag": "🇨🇦"},
    "CHF": {"name": "瑞士法郎", "symbol": "Fr", "flag": "🇨🇭"},
    "HKD": {"name": "港币", "symbol": "HK$", "flag": "🇭🇰"},
    "SGD": {"name": "新加坡元", "symbol": "S$", "flag": "🇸🇬"},
    "KRW": {"name": "韩元", "symbol": "₩", "flag": "🇰🇷"},
    "NZD": {"name": "新西兰元", "symbol": "NZ$", "flag": "🇳🇿"},
    "INR": {"name": "印度卢比", "symbol": "₹", "flag": "🇮🇳"},
    "RUB": {"name": "俄罗斯卢布", "symbol": "₽", "flag": "🇷🇺"},
    "BRL": {"name": "巴西雷亚尔", "symbol": "R$", "flag": "🇧🇷"},
    "ZAR": {"name": "南非兰特", "symbol": "R", "flag": "🇿🇦"},
    "SEK": {"name": "瑞典克朗", "symbol": "kr", "flag": "🇸🇪"},
    "NOK": {"name": "挪威克朗", "symbol": "kr", "flag": "🇳🇴"},
    "DKK": {"name": "丹麦克朗", "symbol": "kr", "flag": "🇩🇰"},
    "MXN": {"name": "墨西哥比索", "symbol": "$", "flag": "🇲🇽"},
    "IDR": {"name": "印尼盾", "symbol": "Rp", "flag": "🇮🇩"},
    "THB": {"name": "泰铢", "symbol": "฿", "flag": "🇹🇭"},
    "MYR": {"name": "马来西亚林吉特", "symbol": "RM", "flag": "🇲🇾"},
    "PHP": {"name": "菲律宾比索", "symbol": "₱", "flag": "🇵🇭"},
    "VND": {"name": "越南盾", "symbol": "₫", "flag": "🇻🇳"},
    "AED": {"name": "阿联酋迪拉姆", "symbol": "د.إ", "flag": "🇦🇪"},
    "SAR": {"name": "沙特里亚尔", "symbol": "ر.س", "flag": "🇸🇦"},
    "TRY": {"name": "土耳其里拉", "symbol": "₺", "flag": "🇹🇷"},
    "PLN": {"name": "波兰兹罗提", "symbol": "zł", "flag": "🇵🇱"},
}

FAVORITE_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CNY", "HKD"]


def create_requests_session() -> requests.Session:
    """创建不使用代理的requests会话"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.trust_env = False
    session.proxies = {
        'http': '',
        'https': '',
    }
    
    return session


class ExchangeRateFetcher:
    """汇率数据获取器"""
    
    @staticmethod
    def format_currency_display(code: str) -> str:
        """格式化货币显示"""
        currency = CURRENCIES.get(code, {})
        name = currency.get("name", code)
        flag = currency.get("flag", "")
        return f"{flag} {code} - {name}"
    
    @classmethod
    def fetch_latest_rates(cls, base_currency: str = "USD") -> Dict[str, Any]:
        """获取最新汇率（使用免费API）"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests库未安装")
        
        api_sources = [
            {
                "name": "ExchangeRate-API",
                "url": f"https://v6.exchangerate-api.com/v6/d850c7a92f1a4b3c2d1e0f9/latest/{base_currency}",
                "parser": lambda data: {
                    "base": data.get("base_code", base_currency),
                    "rates": data.get("conversion_rates", {}),
                    "timestamp": data.get("time_last_update_unix", datetime.now().timestamp())
                }
            },
            {
                "name": "Open Exchange Rates (fallback)",
                "url": f"https://open.er-api.com/v6/latest/{base_currency}",
                "parser": lambda data: {
                    "base": data.get("base_code", base_currency),
                    "rates": data.get("rates", {}),
                    "timestamp": data.get("time_last_update_unix", datetime.now().timestamp())
                }
            }
        ]
        
        session = None
        errors = []
        
        for source in api_sources:
            try:
                session = create_requests_session()
                response = session.get(source["url"], timeout=15, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                }, verify=False)
                response.raise_for_status()
                data = response.json()
                
                if data.get("result") == "success" or data.get("result") == "success":
                    parsed = source["parser"](data)
                    if parsed["rates"]:
                        return {
                            "success": True,
                            "base": parsed["base"],
                            "rates": parsed["rates"],
                            "timestamp": parsed["timestamp"],
                            "source": source["name"]
                        }
                
            except Exception as e:
                errors.append(f"{source['name']}: {str(e)}")
            finally:
                if session:
                    session.close()
        
        raise RuntimeError("所有汇率API都失败了: " + "; ".join(errors))
    
    @classmethod
    def fetch_convert(cls, from_currency: str, to_currency: str, amount: float = 1.0) -> Dict[str, Any]:
        """转换货币"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests库未安装")
        
        url = f"https://v6.exchangerate-api.com/v6/d850c7a92f1a4b3c2d1e0f9/pair/{from_currency}/{to_currency}/{amount}"
        
        session = None
        try:
            session = create_requests_session()
            response = session.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if data.get("result") == "success":
                return {
                    "success": True,
                    "from": from_currency,
                    "to": to_currency,
                    "amount": amount,
                    "rate": data.get("conversion_rate", 0),
                    "result": data.get("conversion_result", 0),
                    "timestamp": data.get("time_last_update_unix", datetime.now().timestamp())
                }
            else:
                raise RuntimeError(f"API返回错误: {data.get('error-type', '未知错误')}")
                
        except Exception as e:
            raise RuntimeError(f"汇率转换失败: {str(e)}")
        finally:
            if session:
                session.close()


class ExchangeRateGenerator:
    """模拟汇率数据生成器（作为备用方案）"""
    
    BASE_RATES = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 155.0,
        "CNY": 7.24,
        "AUD": 1.53,
        "CAD": 1.36,
        "CHF": 0.88,
        "HKD": 7.80,
        "SGD": 1.34,
        "KRW": 1320.0,
        "NZD": 1.64,
        "INR": 83.5,
        "RUB": 92.0,
        "BRL": 5.1,
        "ZAR": 18.5,
        "SEK": 10.5,
        "NOK": 10.8,
        "DKK": 6.85,
        "MXN": 17.2,
        "IDR": 15800.0,
        "THB": 35.0,
        "MYR": 4.7,
        "PHP": 56.0,
        "VND": 25200.0,
        "AED": 3.67,
        "SAR": 3.75,
        "TRY": 32.0,
        "PLN": 3.95,
    }
    
    @classmethod
    def generate_rates(cls, base_currency: str = "USD") -> Dict[str, Any]:
        """生成模拟汇率数据"""
        import random
        random.seed(int(datetime.now().timestamp() // 3600))
        
        base_rate = cls.BASE_RATES.get(base_currency, 1.0)
        
        rates = {}
        for code, rate in cls.BASE_RATES.items():
            variation = 1 + random.uniform(-0.02, 0.02)
            rates[code] = (rate / base_rate) * variation
        
        return {
            "success": True,
            "base": base_currency,
            "rates": rates,
            "timestamp": datetime.now().timestamp(),
            "source": "模拟数据",
            "is_fallback": True
        }
    
    @classmethod
    def convert(cls, from_currency: str, to_currency: str, amount: float) -> Dict[str, Any]:
        """模拟转换货币"""
        rates = cls.generate_rates(from_currency)
        rate = rates["rates"].get(to_currency, 1.0)
        
        return {
            "success": True,
            "from": from_currency,
            "to": to_currency,
            "amount": amount,
            "rate": rate,
            "result": amount * rate,
            "timestamp": datetime.now().timestamp(),
            "source": "模拟数据",
            "is_fallback": True
        }


class CurrencyConverterWorker(QThread):
    """汇率数据获取工作线程"""
    
    data_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, task_type: str, **kwargs):
        super().__init__()
        self.task_type = task_type
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.task_type == "fetch_rates":
                base_currency = self.kwargs.get("base_currency", "USD")
                try:
                    if REQUESTS_AVAILABLE:
                        data = ExchangeRateFetcher.fetch_latest_rates(base_currency)
                    else:
                        data = ExchangeRateGenerator.generate_rates(base_currency)
                except Exception:
                    data = ExchangeRateGenerator.generate_rates(base_currency)
                
                self.data_ready.emit(data)
                
            elif self.task_type == "convert":
                from_currency = self.kwargs.get("from_currency", "USD")
                to_currency = self.kwargs.get("to_currency", "CNY")
                amount = self.kwargs.get("amount", 1.0)
                
                try:
                    if REQUESTS_AVAILABLE:
                        data = ExchangeRateFetcher.fetch_convert(from_currency, to_currency, amount)
                    else:
                        data = ExchangeRateGenerator.convert(from_currency, to_currency, amount)
                except Exception:
                    data = ExchangeRateGenerator.convert(from_currency, to_currency, amount)
                
                self.data_ready.emit(data)
                
        except Exception as e:
            self.error_occurred.emit(str(e))


class CurrencyCard(QFrame):
    """货币卡片组件"""
    
    clicked = pyqtSignal(str)
    
    def __init__(self, currency_code: str, amount: float = 0.0, is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.currency_code = currency_code
        self.amount = amount
        self.is_selected = is_selected
        self._init_ui()
    
    def _init_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(70)
        self._update_style()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        currency = CURRENCIES.get(self.currency_code, {})
        flag = currency.get("flag", "🌍")
        name = currency.get("name", self.currency_code)
        symbol = currency.get("symbol", "")
        
        flag_label = QLabel(flag)
        flag_label.setFont(QFont("Microsoft YaHei", 20))
        layout.addWidget(flag_label)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        code_label = QLabel(self.currency_code)
        code_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        code_label.setStyleSheet(f"color: {'#1565C0' if self.is_selected else '#333333'};")
        info_layout.addWidget(code_label)
        
        name_label = QLabel(name)
        name_label.setFont(QFont("Microsoft YaHei", 10))
        name_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(name_label)
        
        layout.addLayout(info_layout, 1)
        
        amount_layout = QVBoxLayout()
        amount_layout.setSpacing(2)
        amount_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        if self.amount > 0:
            amount_text = f"{symbol} {self.amount:,.2f}"
            amount_label = QLabel(amount_text)
            amount_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
            amount_label.setStyleSheet(f"color: {'#1565C0' if self.is_selected else '#333333'};")
            amount_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            amount_layout.addWidget(amount_label)
        
        layout.addLayout(amount_layout)
    
    def _update_style(self):
        if self.is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #E3F2FD, stop:1 #BBDEFB);
                    border-radius: 10px;
                    border: 2px solid #1565C0;
                }
                QFrame:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #BBDEFB, stop:1 #90CAF9);
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 10px;
                    border: 1px solid #e0e0e0;
                }
                QFrame:hover {
                    border: 1px solid #1565C0;
                    background-color: #FAFAFA;
                }
            """)
    
    def set_selected(self, selected: bool):
        self.is_selected = selected
        self._update_style()
        self.update()
    
    def set_amount(self, amount: float):
        self.amount = amount
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self._init_ui()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.currency_code)
        super().mousePressEvent(event)


class CurrencyConverterMainWidget(QWidget):
    """汇率换算主界面组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = DatabaseManager()
        self._current_rates = {}
        self._base_currency = "CNY"
        self._target_currency = "USD"
        self._amount = 1.0
        self._worker = None
        self._favorite_currencies = self._load_favorites()
        self._init_ui()
        self._create_tables()
        self._load_rates()
    
    def _create_tables(self):
        """创建数据库表"""
        create_favorites_sql = """
        CREATE TABLE IF NOT EXISTS currency_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency_code TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        create_history_sql = """
        CREATE TABLE IF NOT EXISTS currency_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_currency TEXT NOT NULL,
            to_currency TEXT NOT NULL,
            from_amount REAL NOT NULL,
            to_amount REAL NOT NULL,
            rate REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self._db.execute(create_favorites_sql)
        self._db.execute(create_history_sql)
    
    def _load_favorites(self) -> List[str]:
        """加载收藏的货币"""
        try:
            result = self._db.query_all(
                "SELECT currency_code FROM currency_favorites ORDER BY created_at"
            )
            if result:
                return [row['currency_code'] for row in result]
        except Exception:
            pass
        return FAVORITE_CURRENCIES.copy()
    
    def _save_favorite(self, currency_code: str):
        """保存收藏"""
        try:
            self._db.insert('currency_favorites', {
                'currency_code': currency_code
            })
            if currency_code not in self._favorite_currencies:
                self._favorite_currencies.append(currency_code)
        except Exception:
            pass
    
    def _remove_favorite(self, currency_code: str):
        """移除收藏"""
        try:
            self._db.delete('currency_favorites', 'currency_code = ?', (currency_code,))
            if currency_code in self._favorite_currencies:
                self._favorite_currencies.remove(currency_code)
        except Exception:
            pass
    
    def _save_history(self, from_currency: str, to_currency: str, 
                      from_amount: float, to_amount: float, rate: float):
        """保存历史记录"""
        try:
            self._db.insert('currency_history', {
                'from_currency': from_currency,
                'to_currency': to_currency,
                'from_amount': from_amount,
                'to_amount': to_amount,
                'rate': rate
            })
        except Exception:
            pass
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        
        title_label = QLabel("💱 汇率换算")
        title_label.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565C0;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self._refresh_btn = QPushButton("🔄 刷新汇率")
        self._refresh_btn.setMinimumWidth(100)
        self._refresh_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
            QPushButton:disabled {
                background-color: #A5D6A7;
            }
        """)
        self._refresh_btn.clicked.connect(self._on_refresh_rates)
        header_layout.addWidget(self._refresh_btn)
        
        self._swap_btn = QPushButton("⇆ 交换")
        self._swap_btn.setMinimumWidth(80)
        self._swap_btn.setFont(QFont("Microsoft YaHei", 11))
        self._swap_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #EF6C00;
            }
        """)
        self._swap_btn.clicked.connect(self._on_swap_currencies)
        header_layout.addWidget(self._swap_btn)
        
        main_layout.addLayout(header_layout)
        
        info_layout = QHBoxLayout()
        
        self._data_source_label = QLabel("📡 数据来源: 加载中...")
        self._data_source_label.setFont(QFont("Microsoft YaHei", 10))
        self._data_source_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(self._data_source_label)
        
        self._update_time_label = QLabel("⏰ 更新时间: --")
        self._update_time_label.setFont(QFont("Microsoft YaHei", 10))
        self._update_time_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(self._update_time_label)
        
        info_layout.addStretch()
        
        main_layout.addLayout(info_layout)
        
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
        
        converter_tab = self._create_converter_tab()
        self.tab_widget.addTab(converter_tab, "💱 汇率换算")
        
        rates_tab = self._create_rates_tab()
        self.tab_widget.addTab(rates_tab, "📊 汇率列表")
        
        history_tab = self._create_history_tab()
        self.tab_widget.addTab(history_tab, "📜 历史记录")
        
        main_layout.addWidget(self.tab_widget, 1)
    
    def _create_converter_tab(self) -> QWidget:
        """创建汇率换算标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        amount_group = QGroupBox("输入金额")
        amount_group.setStyleSheet("""
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
        
        amount_layout = QVBoxLayout(amount_group)
        amount_layout.setContentsMargins(20, 25, 20, 20)
        amount_layout.setSpacing(15)
        
        input_layout = QHBoxLayout()
        
        amount_label = QLabel("金额:")
        amount_label.setFont(QFont("Microsoft YaHei", 12))
        input_layout.addWidget(amount_label)
        
        self._amount_input = QLineEdit()
        self._amount_input.setMinimumWidth(200)
        self._amount_input.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        self._amount_input.setText("1.00")
        self._amount_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._amount_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #FAFAFA;
                font-size: 18px;
            }
            QLineEdit:focus {
                border-color: #1565C0;
                background-color: white;
            }
        """)
        self._amount_input.textChanged.connect(self._on_amount_changed)
        input_layout.addWidget(self._amount_input)
        
        quick_amounts = ["1", "10", "100", "1000", "10000"]
        for amt in quick_amounts:
            btn = QPushButton(amt)
            btn.setMinimumWidth(60)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border-color: #1565C0;
                }
            """)
            btn.clicked.connect(lambda checked, a=amt: self._set_quick_amount(a))
            input_layout.addWidget(btn)
        
        input_layout.addStretch()
        amount_layout.addLayout(input_layout)
        
        layout.addWidget(amount_group)
        
        convert_group = QGroupBox("货币选择")
        convert_group.setStyleSheet("""
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
        
        convert_layout = QVBoxLayout(convert_group)
        convert_layout.setContentsMargins(20, 25, 20, 20)
        convert_layout.setSpacing(20)
        
        from_layout = QHBoxLayout()
        
        from_label = QLabel("从:")
        from_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        from_label.setStyleSheet("color: #1565C0;")
        from_layout.addWidget(from_label)
        
        self._from_combo = QComboBox()
        self._from_combo.setMinimumWidth(300)
        self._from_combo.setFont(QFont("Microsoft YaHei", 12))
        self._from_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                min-height: 40px;
            }
            QComboBox:hover {
                border-color: #1565C0;
            }
            QComboBox:focus {
                border-color: #1565C0;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 30px;
                border-left: 1px solid #ddd;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: #f5f5f5;
            }
            QComboBox::down-arrow {
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 8px solid #666666;
                margin-right: 5px;
            }
        """)
        self._populate_currency_combo(self._from_combo)
        self._from_combo.setCurrentText(ExchangeRateFetcher.format_currency_display("CNY"))
        self._from_combo.currentIndexChanged.connect(self._on_from_currency_changed)
        from_layout.addWidget(self._from_combo)
        
        swap_icon = QPushButton("⇆")
        swap_icon.setMaximumWidth(50)
        swap_icon.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        swap_icon.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                border-radius: 25px;
                min-height: 50px;
                min-width: 50px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        swap_icon.clicked.connect(self._on_swap_currencies)
        from_layout.addWidget(swap_icon)
        
        to_label = QLabel("到:")
        to_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        to_label.setStyleSheet("color: #E91E63;")
        from_layout.addWidget(to_label)
        
        self._to_combo = QComboBox()
        self._to_combo.setMinimumWidth(300)
        self._to_combo.setFont(QFont("Microsoft YaHei", 12))
        self._to_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                min-height: 40px;
            }
            QComboBox:hover {
                border-color: #E91E63;
            }
            QComboBox:focus {
                border-color: #E91E63;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 30px;
                border-left: 1px solid #ddd;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: #f5f5f5;
            }
            QComboBox::down-arrow {
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 8px solid #666666;
                margin-right: 5px;
            }
        """)
        self._populate_currency_combo(self._to_combo)
        self._to_combo.setCurrentText(ExchangeRateFetcher.format_currency_display("USD"))
        self._to_combo.currentIndexChanged.connect(self._on_to_currency_changed)
        from_layout.addWidget(self._to_combo)
        
        from_layout.addStretch()
        convert_layout.addLayout(from_layout)
        
        layout.addWidget(convert_group)
        
        result_group = QGroupBox("换算结果")
        result_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #E8F5E9, stop:1 #C8E6C9);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #2E7D32;
            }
        """)
        
        result_layout = QVBoxLayout(result_group)
        result_layout.setContentsMargins(20, 25, 20, 20)
        result_layout.setSpacing(15)
        
        self._result_display = QLabel("请选择货币并输入金额进行换算...")
        self._result_display.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        self._result_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_display.setStyleSheet("color: #2E7D32; padding: 20px;")
        result_layout.addWidget(self._result_display)
        
        self._rate_display = QLabel("")
        self._rate_display.setFont(QFont("Microsoft YaHei", 12))
        self._rate_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._rate_display.setStyleSheet("color: #558B2F;")
        result_layout.addWidget(self._rate_display)
        
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self._favorite_btn = QPushButton("⭐ 添加到收藏")
        self._favorite_btn.setMinimumWidth(120)
        self._favorite_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFB300;
            }
            QPushButton:pressed {
                background-color: #FF8F00;
            }
        """)
        self._favorite_btn.clicked.connect(self._on_toggle_favorite)
        action_layout.addWidget(self._favorite_btn)
        
        self._convert_btn = QPushButton("💱 立即换算")
        self._convert_btn.setMinimumWidth(120)
        self._convert_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self._convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #90CAF9;
            }
        """)
        self._convert_btn.clicked.connect(self._on_convert)
        action_layout.addWidget(self._convert_btn)
        
        action_layout.addStretch()
        result_layout.addLayout(action_layout)
        
        layout.addWidget(result_group)
        
        return widget
    
    def _create_rates_tab(self) -> QWidget:
        """创建汇率列表标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        filter_layout = QHBoxLayout()
        
        base_label = QLabel("基准货币:")
        base_label.setFont(QFont("Microsoft YaHei", 11))
        filter_layout.addWidget(base_label)
        
        self._base_combo = QComboBox()
        self._base_combo.setMinimumWidth(250)
        self._base_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #1565C0;
            }
        """)
        self._populate_currency_combo(self._base_combo)
        self._base_combo.setCurrentText(ExchangeRateFetcher.format_currency_display("CNY"))
        self._base_combo.currentIndexChanged.connect(self._on_base_currency_changed)
        filter_layout.addWidget(self._base_combo)
        
        filter_layout.addStretch()
        
        search_label = QLabel("搜索:")
        search_label.setFont(QFont("Microsoft YaHei", 11))
        filter_layout.addWidget(search_label)
        
        self._search_input = QLineEdit()
        self._search_input.setMinimumWidth(200)
        self._search_input.setPlaceholderText("输入货币代码或名称...")
        self._search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border-color: #1565C0;
            }
        """)
        self._search_input.textChanged.connect(self._filter_rates)
        filter_layout.addWidget(self._search_input)
        
        layout.addLayout(filter_layout)
        
        self._rates_scroll = QScrollArea()
        self._rates_scroll.setWidgetResizable(True)
        self._rates_scroll.setStyleSheet("""
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
        
        self._rates_container = QWidget()
        self._rates_container_layout = QVBoxLayout(self._rates_container)
        self._rates_container_layout.setContentsMargins(5, 5, 5, 5)
        self._rates_container_layout.setSpacing(10)
        
        self._rates_scroll.setWidget(self._rates_container)
        layout.addWidget(self._rates_scroll, 1)
        
        return widget
    
    def _create_history_tab(self) -> QWidget:
        """创建历史记录标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        toolbar_layout = QHBoxLayout()
        
        toolbar_layout.addStretch()
        
        self._clear_history_btn = QPushButton("🗑️ 清空历史")
        self._clear_history_btn.setStyleSheet("""
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
        self._clear_history_btn.clicked.connect(self._on_clear_history)
        toolbar_layout.addWidget(self._clear_history_btn)
        
        layout.addLayout(toolbar_layout)
        
        self._history_list = QListWidget()
        self._history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                padding: 5px;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #f0f0f0;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
            }
            QListWidget::item:hover {
                background-color: #FAFAFA;
            }
        """)
        layout.addWidget(self._history_list, 1)
        
        self._load_history()
        
        return widget
    
    def _populate_currency_combo(self, combo: QComboBox):
        """填充货币下拉框"""
        combo.clear()
        
        for code in self._favorite_currencies:
            if code in CURRENCIES:
                combo.addItem(ExchangeRateFetcher.format_currency_display(code), code)
        
        combo.insertSeparator(len(self._favorite_currencies))
        
        for code in sorted(CURRENCIES.keys()):
            if code not in self._favorite_currencies:
                combo.addItem(ExchangeRateFetcher.format_currency_display(code), code)
    
    def _load_rates(self):
        """加载汇率数据"""
        self._refresh_btn.setEnabled(False)
        self._refresh_btn.setText("加载中...")
        self._convert_btn.setEnabled(False)
        self._data_source_label.setText("📡 数据来源: 正在查询...")
        
        self._worker = CurrencyConverterWorker("fetch_rates", base_currency=self._base_currency)
        self._worker.data_ready.connect(self._on_rates_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()
    
    def _on_rates_ready(self, data: Dict[str, Any]):
        """汇率数据准备就绪"""
        self._current_rates = data.get("rates", {})
        
        source = data.get("source", "未知")
        is_fallback = data.get("is_fallback", False)
        
        if is_fallback:
            self._data_source_label.setText(f"📡 数据来源: {source} (离线模式)")
            self._data_source_label.setStyleSheet("color: #FF9800;")
        else:
            self._data_source_label.setText(f"📡 数据来源: {source}")
            self._data_source_label.setStyleSheet("color: #4CAF50;")
        
        timestamp = data.get("timestamp")
        if timestamp:
            update_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            self._update_time_label.setText(f"⏰ 更新时间: {update_time}")
        
        self._refresh_btn.setEnabled(True)
        self._refresh_btn.setText("🔄 刷新汇率")
        self._convert_btn.setEnabled(True)
        
        self._update_rates_list()
        self._perform_conversion()
    
    def _on_error(self, error_msg: str):
        """处理错误"""
        QMessageBox.warning(self, "警告", f"获取汇率数据时出错: {error_msg}\n将使用模拟数据。")
        self._refresh_btn.setEnabled(True)
        self._refresh_btn.setText("🔄 刷新汇率")
    
    def _on_refresh_rates(self):
        """刷新汇率"""
        self._load_rates()
    
    def _on_swap_currencies(self):
        """交换货币"""
        from_index = self._from_combo.currentIndex()
        to_index = self._to_combo.currentIndex()
        
        from_data = self._from_combo.itemData(from_index)
        to_data = self._to_combo.itemData(to_index)
        
        for i in range(self._from_combo.count()):
            if self._from_combo.itemData(i) == to_data:
                self._from_combo.setCurrentIndex(i)
                break
        
        for i in range(self._to_combo.count()):
            if self._to_combo.itemData(i) == from_data:
                self._to_combo.setCurrentIndex(i)
                break
    
    def _on_from_currency_changed(self, index: int):
        """源货币改变"""
        code = self._from_combo.itemData(index)
        if code:
            self._base_currency = code
            self._perform_conversion()
            self._update_favorite_button()
    
    def _on_to_currency_changed(self, index: int):
        """目标货币改变"""
        code = self._to_combo.itemData(index)
        if code:
            self._target_currency = code
            self._perform_conversion()
            self._update_favorite_button()
    
    def _on_base_currency_changed(self, index: int):
        """基准货币改变"""
        code = self._base_combo.itemData(index)
        if code:
            self._base_currency = code
            self._load_rates()
    
    def _on_amount_changed(self, text: str):
        """金额改变"""
        try:
            self._amount = float(text) if text else 0.0
            self._perform_conversion()
        except ValueError:
            pass
    
    def _set_quick_amount(self, amount: str):
        """设置快捷金额"""
        self._amount_input.setText(amount)
    
    def _on_convert(self):
        """执行换算"""
        self._perform_conversion(save_history=True)
    
    def _perform_conversion(self, save_history: bool = False):
        """执行换算逻辑"""
        if not self._current_rates:
            return
        
        try:
            from_code = self._base_currency
            to_code = self._target_currency
            amount = self._amount
            
            if from_code == to_code:
                result = amount
                rate = 1.0
            else:
                if from_code in self._current_rates:
                    from_rate = self._current_rates[from_code]
                else:
                    from_rate = 1.0
                
                if to_code in self._current_rates:
                    to_rate = self._current_rates[to_code]
                else:
                    to_rate = 1.0
                
                rate = to_rate / from_rate if from_rate != 0 else 0
                result = amount * rate
            
            from_currency = CURRENCIES.get(from_code, {})
            to_currency = CURRENCIES.get(to_code, {})
            
            from_symbol = from_currency.get("symbol", from_code)
            to_symbol = to_currency.get("symbol", to_code)
            from_name = from_currency.get("name", from_code)
            to_name = to_currency.get("name", to_code)
            from_flag = from_currency.get("flag", "")
            to_flag = to_currency.get("flag", "")
            
            result_text = (
                f"{from_flag} {from_symbol} {amount:,.2f} {from_code} ({from_name})"
                f"  =  "
                f"{to_flag} {to_symbol} {result:,.4f} {to_code} ({to_name})"
            )
            self._result_display.setText(result_text)
            
            rate_text = f"汇率: 1 {from_code} = {rate:.6f} {to_code}"
            self._rate_display.setText(rate_text)
            
            if save_history:
                self._save_history(from_code, to_code, amount, result, rate)
                self._load_history()
                
        except Exception as e:
            self._result_display.setText(f"换算出错: {str(e)}")
    
    def _update_rates_list(self):
        """更新汇率列表"""
        for i in reversed(range(self._rates_container_layout.count())):
            item = self._rates_container_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        if not self._current_rates:
            no_data_label = QLabel("暂无汇率数据")
            no_data_label.setFont(QFont("Microsoft YaHei", 14))
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_label.setStyleSheet("color: #999999; padding: 50px;")
            self._rates_container_layout.addWidget(no_data_label)
            return
        
        filter_text = self._search_input.text().lower() if hasattr(self, '_search_input') else ""
        
        for code in sorted(CURRENCIES.keys()):
            if code == self._base_currency:
                continue
            
            currency = CURRENCIES.get(code, {})
            name = currency.get("name", code)
            
            if filter_text:
                if filter_text not in code.lower() and filter_text not in name.lower():
                    continue
            
            rate = self._current_rates.get(code, 0)
            if rate > 0:
                inverse_rate = 1.0 / rate
            else:
                inverse_rate = 0
            
            card = CurrencyCard(code, rate)
            card.setToolTip(f"1 {self._base_currency} = {rate:.4f} {code}\n1 {code} = {inverse_rate:.6f} {self._base_currency}")
            self._rates_container_layout.addWidget(card)
        
        self._rates_container_layout.addStretch()
    
    def _filter_rates(self):
        """过滤汇率列表"""
        self._update_rates_list()
    
    def _update_favorite_button(self):
        """更新收藏按钮状态"""
        if self._target_currency in self._favorite_currencies:
            self._favorite_btn.setText("⭐ 已收藏")
            self._favorite_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9E9E9E;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
        else:
            self._favorite_btn.setText("⭐ 添加到收藏")
            self._favorite_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFC107;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FFB300;
                }
                QPushButton:pressed {
                    background-color: #FF8F00;
                }
            """)
    
    def _on_toggle_favorite(self):
        """切换收藏状态"""
        if self._target_currency in self._favorite_currencies:
            self._remove_favorite(self._target_currency)
        else:
            self._save_favorite(self._target_currency)
        
        self._update_favorite_button()
        
        current_from = self._from_combo.currentData()
        current_to = self._to_combo.currentData()
        current_base = self._base_combo.currentData()
        
        self._populate_currency_combo(self._from_combo)
        self._populate_currency_combo(self._to_combo)
        self._populate_currency_combo(self._base_combo)
        
        for i in range(self._from_combo.count()):
            if self._from_combo.itemData(i) == current_from:
                self._from_combo.setCurrentIndex(i)
                break
        
        for i in range(self._to_combo.count()):
            if self._to_combo.itemData(i) == current_to:
                self._to_combo.setCurrentIndex(i)
                break
        
        for i in range(self._base_combo.count()):
            if self._base_combo.itemData(i) == current_base:
                self._base_combo.setCurrentIndex(i)
                break
    
    def _load_history(self):
        """加载历史记录"""
        self._history_list.clear()
        
        try:
            history = self._db.query_all(
                "SELECT * FROM currency_history ORDER BY created_at DESC LIMIT 50"
            )
            
            if not history:
                item = QListWidgetItem("暂无历史记录")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self._history_list.addItem(item)
                return
            
            for record in history:
                from_code = record['from_currency']
                to_code = record['to_currency']
                from_amount = record['from_amount']
                to_amount = record['to_amount']
                rate = record['rate']
                created_at = record['created_at']
                
                from_currency = CURRENCIES.get(from_code, {})
                to_currency = CURRENCIES.get(to_code, {})
                
                from_flag = from_currency.get("flag", "")
                to_flag = to_currency.get("flag", "")
                from_symbol = from_currency.get("symbol", from_code)
                to_symbol = to_currency.get("symbol", to_code)
                
                text = (
                    f"{from_flag} {from_symbol} {from_amount:,.2f} {from_code}  →  "
                    f"{to_flag} {to_symbol} {to_amount:,.4f} {to_code}\n"
                    f"   汇率: 1 {from_code} = {rate:.6f} {to_code} | {created_at}"
                )
                
                item = QListWidgetItem(text)
                item.setFont(QFont("Microsoft YaHei", 11))
                self._history_list.addItem(item)
                
        except Exception as e:
            print(f"加载历史记录失败: {e}")
    
    def _on_clear_history(self):
        """清空历史记录"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._db.execute("DELETE FROM currency_history")
                self._load_history()
                QMessageBox.information(self, "成功", "历史记录已清空！")
            except Exception as e:
                QMessageBox.warning(self, "警告", f"清空历史记录失败: {e}")


class CurrencyConverterModule(BaseModule):
    """
    汇率换算模块
    提供实时汇率查询和货币换算功能
    """
    
    @property
    def module_id(self) -> str:
        return "currency_converter"
    
    @property
    def name(self) -> str:
        return "汇率换算"
    
    @property
    def description(self) -> str:
        return "实时汇率查询和货币换算工具，支持多种货币，界面美观实用"
    
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
    
    def _on_unload(self) -> None:
        """
        模块卸载时的清理
        """
        pass
    
    def _create_widget(self) -> QWidget:
        """
        创建汇率换算的主界面
        """
        return CurrencyConverterMainWidget()
