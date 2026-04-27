#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气查询模块
生活工具分类下的天气查询功能
"""

import json
import random
import os
import urllib3
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


class OpenMeteoWeatherFetcher:
    """Open-Meteo天气数据获取器（免费、无API密钥、支持中文城市名）"""
    
    WEATHER_CODE_MAP = {
        0: ("晴", "☀️"),
        1: ("大部晴朗", "🌤️"),
        2: ("多云", "⛅"),
        3: ("阴", "☁️"),
        45: ("雾", "🌫️"),
        48: ("雾凇", "🌫️"),
        51: ("小毛毛雨", "🌧️"),
        53: ("毛毛雨", "🌧️"),
        55: ("大毛毛雨", "🌧️"),
        56: ("冻毛毛雨", "🌧️"),
        57: ("大冻毛毛雨", "🌧️"),
        61: ("小雨", "🌧️"),
        63: ("中雨", "🌧️"),
        65: ("大雨", "🌧️"),
        66: ("冻雨", "🌧️"),
        67: ("大冻雨", "🌧️"),
        71: ("小雪", "❄️"),
        73: ("中雪", "❄️"),
        75: ("大雪", "❄️"),
        77: "雪粒",
        80: ("小阵雨", "🌧️"),
        81: ("阵雨", "🌧️"),
        82: ("强阵雨", "🌧️"),
        85: ("小阵雪", "❄️"),
        86: ("大阵雪", "❄️"),
        95: ("雷阵雨", "⛈️"),
        96: ("雷阵雨伴小冰雹", "⛈️"),
        99: ("雷阵雨伴大冰雹", "⛈️"),
    }
    
    WIND_DIRECTION_MAP = {
        0: "北风",
        45: "东北风",
        90: "东风",
        135: "东南风",
        180: "南风",
        225: "西南风",
        270: "西风",
        315: "西北风",
    }
    
    @classmethod
    def get_weather_condition(cls, weather_code: int) -> tuple:
        """根据天气代码获取天气状况和图标"""
        result = cls.WEATHER_CODE_MAP.get(weather_code)
        if result is None:
            if weather_code < 45:
                return ("晴", "☀️")
            elif weather_code < 60:
                return ("雾", "🌫️")
            elif weather_code < 70:
                return ("雨", "🌧️")
            elif weather_code < 80:
                return ("雪", "❄️")
            else:
                return ("雷阵雨", "⛈️")
        if isinstance(result, tuple):
            return result
        return (result, "🌤️")
    
    @classmethod
    def get_wind_direction(cls, degrees: float) -> str:
        """根据风向角度获取中文风向"""
        if degrees < 0:
            degrees += 360
        degrees = degrees % 360
        
        min_diff = 360
        closest_dir = 0
        for angle in cls.WIND_DIRECTION_MAP.keys():
            diff = abs(degrees - angle)
            if diff > 180:
                diff = 360 - diff
            if diff < min_diff:
                min_diff = diff
                closest_dir = angle
        
        return cls.WIND_DIRECTION_MAP[closest_dir]
    
    @classmethod
    def geocode_city(cls, city_name: str, language: str = "zh") -> Optional[Dict[str, Any]]:
        """通过城市名称获取地理坐标（Open-Meteo地理编码API）"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests库未安装")
        
        import urllib.parse
        encoded_city = urllib.parse.quote(city_name)
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=5&language={language}&format=json"
        
        session = None
        try:
            session = create_requests_session()
            response = session.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }, verify=False)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if not results:
                return None
            
            return results[0]
            
        except Exception as e:
            error_msg = str(e)
            if "SSL" in error_msg or "ssl" in error_msg:
                raise RuntimeError(f"地理编码失败 (SSL错误): {error_msg}")
            elif "Proxy" in error_msg or "proxy" in error_msg:
                raise RuntimeError(f"地理编码失败 (代理错误): {error_msg}")
            elif "Connection" in error_msg or "connection" in error_msg:
                raise RuntimeError(f"地理编码失败 (连接错误): {error_msg}")
            else:
                raise RuntimeError(f"地理编码失败: {error_msg}")
        finally:
            if session:
                session.close()
    
    @classmethod
    def fetch_weather_by_coords(cls, latitude: float, longitude: float, 
                                  city_name: str = "", days: int = 7) -> List[Dict[str, Any]]:
        """通过经纬度获取天气预报"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests库未安装")
        
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
            f"precipitation,weather_code,pressure_msl,wind_speed_10m,wind_direction_10m,"
            f"cloud_cover,visibility"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
            f"precipitation_sum,uv_index_max,wind_speed_10m_max,wind_direction_10m_dominant"
            f"&timezone=auto"
            f"&forecast_days={days}"
        )
        
        session = None
        try:
            session = create_requests_session()
            response = session.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }, verify=False)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            daily = data.get("daily", {})
            forecast = []
            today = datetime.now()
            
            dates = daily.get("time", [])
            weather_codes = daily.get("weather_code", [])
            temp_max = daily.get("temperature_2m_max", [])
            temp_min = daily.get("temperature_2m_min", [])
            precip_sum = daily.get("precipitation_sum", [])
            uv_index = daily.get("uv_index_max", [])
            wind_speed_max = daily.get("wind_speed_10m_max", [])
            wind_dir_dominant = daily.get("wind_direction_10m_dominant", [])
            
            for i in range(min(days, len(dates))):
                date_str = dates[i] if i < len(dates) else ""
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    date = today + timedelta(days=i)
                
                code = weather_codes[i] if i < len(weather_codes) else 0
                condition, icon = cls.get_weather_condition(code)
                
                high = temp_max[i] if i < len(temp_max) else 20
                low = temp_min[i] if i < len(temp_min) else 10
                precip = precip_sum[i] if i < len(precip_sum) else 0
                uv = uv_index[i] if i < len(uv_index) else 0
                wind_speed = wind_speed_max[i] if i < len(wind_speed_max) else 10
                wind_dir_deg = wind_dir_dominant[i] if i < len(wind_dir_dominant) else 0
                
                if i == 0:
                    temp_current = current.get("temperature_2m", (high + low) / 2)
                    humidity = current.get("relative_humidity_2m", 50)
                    pressure = current.get("pressure_msl", 1013)
                    visibility_km = current.get("visibility", 10000) / 1000 if current.get("visibility") else 10
                else:
                    temp_current = (high + low) / 2
                    humidity = 50 + int(precip * 5)
                    pressure = 1013
                    visibility_km = 10 if precip < 1 else 5
                
                weather_dict = {
                    "city": city_name,
                    "date": date.strftime("%Y-%m-%d"),
                    "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()],
                    "condition": condition,
                    "icon": icon,
                    "temp_high": int(round(high)),
                    "temp_low": int(round(low)),
                    "temp_current": int(round(temp_current)),
                    "humidity": int(humidity),
                    "wind_speed": int(round(wind_speed)),
                    "wind_direction": cls.get_wind_direction(wind_dir_deg),
                    "visibility": int(round(visibility_km)),
                    "pressure": int(round(pressure)),
                    "uv_index": int(round(uv)),
                    "aqi": cls._estimate_aqi(humidity, visibility_km),
                    "precipitation": precip,
                }
                
                if i == 0:
                    weather_dict["is_today"] = True
                elif i == 1:
                    weather_dict["is_tomorrow"] = True
                
                forecast.append(weather_dict)
            
            return forecast
            
        except Exception as e:
            error_msg = str(e)
            if "SSL" in error_msg or "ssl" in error_msg:
                raise RuntimeError(f"获取天气数据失败 (SSL错误): {error_msg}")
            elif "Proxy" in error_msg or "proxy" in error_msg:
                raise RuntimeError(f"获取天气数据失败 (代理错误): {error_msg}")
            elif "Connection" in error_msg or "connection" in error_msg:
                raise RuntimeError(f"获取天气数据失败 (连接错误): {error_msg}")
            else:
                raise RuntimeError(f"获取天气数据失败: {error_msg}")
        finally:
            if session:
                session.close()
    
    @classmethod
    def fetch_forecast(cls, city_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """通过城市名称获取天气预报（自动地理编码）"""
        location = cls.geocode_city(city_name)
        if location is None:
            raise RuntimeError(f"无法找到城市: {city_name}")
        
        lat = location.get("latitude")
        lon = location.get("longitude")
        
        display_name = location.get("name", city_name)
        admin1 = location.get("admin1", "")
        country = location.get("country", "")
        if admin1 and display_name != admin1:
            display_name = f"{display_name}, {admin1}"
        
        return cls.fetch_weather_by_coords(lat, lon, display_name, days)
    
    @classmethod
    def fetch_current_weather(cls, city_name: str) -> Dict[str, Any]:
        """获取当前天气"""
        forecast = cls.fetch_forecast(city_name, 1)
        if forecast:
            return forecast[0]
        raise RuntimeError("无法获取当前天气")
    
    @classmethod
    def _estimate_aqi(cls, humidity: float, visibility_km: float) -> int:
        """根据湿度和能见度估算空气质量指数"""
        if visibility_km >= 20 and humidity <= 60:
            return random.randint(20, 50)
        elif visibility_km >= 10 and humidity <= 70:
            return random.randint(50, 100)
        elif visibility_km >= 5 and humidity <= 80:
            return random.randint(100, 150)
        else:
            return random.randint(150, 200)


class RealWeatherFetcher:
    """真实天气数据获取器（使用wttr.in API）"""
    
    WEATHER_CODE_MAP = {
        113: ("晴", "☀️"),
        116: ("多云", "⛅"),
        119: ("阴", "☁️"),
        122: ("阴", "☁️"),
        143: ("雾", "🌫️"),
        176: ("小雨", "🌧️"),
        179: ("小雪", "❄️"),
        182: ("小雨", "🌧️"),
        185: ("小雨", "🌧️"),
        200: ("雷阵雨", "⛈️"),
        227: ("小雪", "❄️"),
        230: ("大雪", "❄️"),
        248: ("雾", "🌫️"),
        260: ("雾", "🌫️"),
        263: ("小雨", "🌧️"),
        266: ("小雨", "🌧️"),
        281: ("小雨", "🌧️"),
        284: ("小雨", "🌧️"),
        293: ("小雨", "🌧️"),
        296: ("小雨", "🌧️"),
        299: ("中雨", "🌧️"),
        302: ("中雨", "🌧️"),
        305: ("大雨", "🌧️"),
        308: ("大雨", "🌧️"),
        311: ("小雨", "🌧️"),
        314: ("中雨", "🌧️"),
        317: ("小雨", "🌧️"),
        320: ("小雪", "❄️"),
        323: ("小雪", "❄️"),
        326: ("小雪", "❄️"),
        329: ("中雪", "❄️"),
        332: ("中雪", "❄️"),
        335: ("大雪", "❄️"),
        338: ("大雪", "❄️"),
        350: ("小雨", "🌧️"),
        353: ("小雨", "🌧️"),
        356: ("中雨", "🌧️"),
        359: ("大雨", "🌧️"),
        362: ("小雨", "🌧️"),
        365: ("中雨", "🌧️"),
        368: ("小雪", "❄️"),
        371: ("中雪", "❄️"),
        374: ("小雨", "🌧️"),
        377: ("小雨", "🌧️"),
        386: ("雷阵雨", "⛈️"),
        389: ("雷阵雨", "⛈️"),
        392: ("雷阵雨", "⛈️"),
        395: ("雷阵雨", "⛈️"),
    }
    
    WIND_DIRECTION_MAP = {
        "N": "北风",
        "NE": "东北风",
        "E": "东风",
        "SE": "东南风",
        "S": "南风",
        "SW": "西南风",
        "W": "西风",
        "NW": "西北风",
        "NNE": "东北偏北风",
        "ENE": "东北偏东风",
        "ESE": "东南偏东风",
        "SSE": "东南偏南风",
        "SSW": "西南偏南风",
        "WSW": "西南偏西风",
        "WNW": "西北偏西风",
        "NNW": "西北偏北风",
    }
    
    @classmethod
    def get_weather_condition(cls, weather_code: int) -> tuple:
        """根据天气代码获取天气状况和图标"""
        return cls.WEATHER_CODE_MAP.get(weather_code, ("晴", "☀️"))
    
    @classmethod
    def get_wind_direction(cls, wind_dir: str) -> str:
        """获取中文风向"""
        return cls.WIND_DIRECTION_MAP.get(wind_dir, wind_dir)
    
    @classmethod
    def fetch_current_weather(cls, city_name: str) -> Dict[str, Any]:
        """获取当前天气数据"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests库未安装，无法获取真实天气数据")
        
        import urllib.parse
        encoded_city = urllib.parse.quote(city_name)
        url = f"https://wttr.in/{encoded_city}?format=j1&m"
        
        session = None
        try:
            session = create_requests_session()
            response = session.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }, verify=False)
            response.raise_for_status()
            data = response.json()
            
            current_condition = data.get("current_condition", [{}])[0]
            weather_list = data.get("weather", [])
            today_weather = weather_list[0] if weather_list else {}
            
            temp_current = int(current_condition.get("temp_C", 0))
            temp_high = int(today_weather.get("maxtempC", temp_current + 5))
            temp_low = int(today_weather.get("mintempC", temp_current - 5))
            
            weather_code = int(current_condition.get("weatherCode", 113))
            condition, icon = cls.get_weather_condition(weather_code)
            
            humidity = int(current_condition.get("humidity", 50))
            wind_speed = int(current_condition.get("windspeedKmph", 10))
            wind_dir = cls.get_wind_direction(current_condition.get("winddir16Point", "N"))
            visibility = int(current_condition.get("visibility", 10))
            pressure = int(current_condition.get("pressure", 1013))
            
            uv_index = int(current_condition.get("uvIndex", 0)) if current_condition.get("uvIndex") else 0
            
            return {
                "city": city_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()],
                "condition": condition,
                "icon": icon,
                "temp_high": temp_high,
                "temp_low": temp_low,
                "temp_current": temp_current,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "wind_direction": wind_dir,
                "visibility": visibility,
                "pressure": pressure,
                "uv_index": uv_index,
                "aqi": cls._estimate_aqi(humidity, visibility),
                "is_today": True,
            }
            
        except Exception as e:
            error_msg = str(e)
            if "SSL" in error_msg or "ssl" in error_msg:
                raise RuntimeError(f"获取天气数据失败 (SSL错误): {error_msg}")
            elif "Proxy" in error_msg or "proxy" in error_msg:
                raise RuntimeError(f"获取天气数据失败 (代理错误): {error_msg}")
            elif "Connection" in error_msg or "connection" in error_msg:
                raise RuntimeError(f"获取天气数据失败 (连接错误): {error_msg}")
            else:
                raise RuntimeError(f"获取天气数据失败: {error_msg}")
        finally:
            if session:
                session.close()
    
    @classmethod
    def fetch_forecast(cls, city_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """获取未来天气预报"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests库未安装，无法获取真实天气数据")
        
        import urllib.parse
        encoded_city = urllib.parse.quote(city_name)
        url = f"https://wttr.in/{encoded_city}?format=j1&m"
        
        session = None
        try:
            session = create_requests_session()
            response = session.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }, verify=False)
            response.raise_for_status()
            data = response.json()
            
            weather_list = data.get("weather", [])
            forecast = []
            today = datetime.now()
            
            for i in range(min(days, len(weather_list))):
                weather_data = weather_list[i]
                date = today + timedelta(days=i)
                
                max_temp = int(weather_data.get("maxtempC", 20))
                min_temp = int(weather_data.get("mintempC", 10))
                
                hourly = weather_data.get("hourly", [])
                if hourly:
                    midday_hour = hourly[len(hourly) // 2] if len(hourly) > 0 else {}
                    weather_code = int(midday_hour.get("weatherCode", 113))
                    humidity = int(midday_hour.get("humidity", 50))
                    wind_speed = int(midday_hour.get("windspeedKmph", 10))
                    wind_dir = cls.get_wind_direction(midday_hour.get("winddir16Point", "N"))
                    visibility = int(midday_hour.get("visibility", 10))
                    pressure = int(midday_hour.get("pressure", 1013))
                    uv_index = int(midday_hour.get("uvIndex", 0)) if midday_hour.get("uvIndex") else 0
                else:
                    weather_code = 113
                    humidity = 50
                    wind_speed = 10
                    wind_dir = "N"
                    visibility = 10
                    pressure = 1013
                    uv_index = 0
                
                condition, icon = cls.get_weather_condition(weather_code)
                
                weather_dict = {
                    "city": city_name,
                    "date": date.strftime("%Y-%m-%d"),
                    "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()],
                    "condition": condition,
                    "icon": icon,
                    "temp_high": max_temp,
                    "temp_low": min_temp,
                    "temp_current": (max_temp + min_temp) // 2,
                    "humidity": humidity,
                    "wind_speed": wind_speed,
                    "wind_direction": wind_dir,
                    "visibility": visibility,
                    "pressure": pressure,
                    "uv_index": uv_index,
                    "aqi": cls._estimate_aqi(humidity, visibility),
                }
                
                if i == 0:
                    weather_dict["is_today"] = True
                elif i == 1:
                    weather_dict["is_tomorrow"] = True
                
                forecast.append(weather_dict)
            
            return forecast
            
        except Exception as e:
            error_msg = str(e)
            if "SSL" in error_msg or "ssl" in error_msg:
                raise RuntimeError(f"获取天气预报失败 (SSL错误): {error_msg}")
            elif "Proxy" in error_msg or "proxy" in error_msg:
                raise RuntimeError(f"获取天气预报失败 (代理错误): {error_msg}")
            elif "Connection" in error_msg or "connection" in error_msg:
                raise RuntimeError(f"获取天气预报失败 (连接错误): {error_msg}")
            else:
                raise RuntimeError(f"获取天气预报失败: {error_msg}")
        finally:
            if session:
                session.close()
    
    @classmethod
    def _estimate_aqi(cls, humidity: int, visibility: int) -> int:
        """根据湿度和能见度估算空气质量指数"""
        if visibility >= 20 and humidity <= 60:
            return random.randint(20, 50)
        elif visibility >= 10 and humidity <= 70:
            return random.randint(50, 100)
        elif visibility >= 5 and humidity <= 80:
            return random.randint(100, 150)
        else:
            return random.randint(150, 200)


class WeatherDataGenerator:
    """天气数据生成器（模拟数据 - 作为备用方案）"""
    
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
    
    def __init__(self, city_name: str, data_type: str = "forecast", days: int = 7, use_real_api: bool = True):
        super().__init__()
        self.city_name = city_name
        self.data_type = data_type
        self.days = days
        self.use_real_api = use_real_api
    
    def run(self):
        try:
            data = []
            use_fallback = False
            error_msg = ""
            api_used = None
            api_errors = []
            
            if self.use_real_api and REQUESTS_AVAILABLE:
                if self.data_type == "forecast":
                    try:
                        data = OpenMeteoWeatherFetcher.fetch_forecast(self.city_name, self.days)
                        api_used = "Open-Meteo"
                    except Exception as e:
                        api_errors.append(f"Open-Meteo: {str(e)}")
                        try:
                            data = RealWeatherFetcher.fetch_forecast(self.city_name, self.days)
                            api_used = "wttr.in"
                        except Exception as e2:
                            api_errors.append(f"wttr.in: {str(e2)}")
                            error_msg = "; ".join(api_errors)
                            use_fallback = True
                elif self.data_type == "history":
                    data = WeatherDataGenerator.generate_history(self.city_name, self.days)
                    api_used = "模拟数据(历史)"
                else:
                    data = []
            else:
                use_fallback = True
                error_msg = "requests库未安装" if not REQUESTS_AVAILABLE else "未启用真实API"
            
            if use_fallback:
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
                "type": self.data_type,
                "used_real_api": api_used is not None and api_used not in ["模拟数据(历史)"],
                "api_used": api_used,
                "fallback_message": error_msg if use_fallback else None
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
        self._data_source_label = None
        self._last_update_label = None
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        title_label = QLabel("🌤️ 天气查询")
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
        self.city_combo.setMinimumWidth(180)
        self.city_combo.setFont(QFont("Microsoft YaHei", 11))
        self.city_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 30px 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #1565C0;
            }
            QComboBox:focus {
                border-color: #1565C0;
                border-width: 2px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 25px;
                border-left: 1px solid #ddd;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background-color: #f5f5f5;
            }
            QComboBox::drop-down:hover {
                background-color: #e0e0e0;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #666666;
                margin-right: 5px;
            }
            QComboBox::down-arrow:on {
                border-top: none;
                border-bottom: 6px solid #666666;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #1565C0;
                selection-color: white;
                padding: 5px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 25px;
                padding: 5px 10px;
            }
        """)
        
        popular_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉", "西安", "重庆", "天津", "苏州", "长沙", "郑州", "东莞", "青岛", "沈阳", "宁波", "昆明"]
        self.city_combo.addItems(popular_cities)
        self.city_combo.setCurrentText("北京")
        self.city_combo.lineEdit().setPlaceholderText("输入城市名称...")
        self.city_combo.activated.connect(self._on_city_selected)
        self.city_combo.lineEdit().returnPressed.connect(self._on_search)
        header_layout.addWidget(self.city_combo)
        
        self.search_btn = QPushButton("🔍 查询")
        self.search_btn.setMinimumWidth(90)
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
            QPushButton:disabled {
                background-color: #90CAF9;
            }
        """)
        self.search_btn.clicked.connect(self._on_search)
        header_layout.addWidget(self.search_btn)
        
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setMinimumWidth(80)
        self.refresh_btn.setFont(QFont("Microsoft YaHei", 11))
        self.refresh_btn.setStyleSheet("""
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
        self.refresh_btn.clicked.connect(self._on_refresh)
        header_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        info_bar_layout = QHBoxLayout()
        info_bar_layout.setSpacing(15)
        
        self._data_source_label = QLabel("📡 数据来源: 加载中...")
        self._data_source_label.setFont(QFont("Microsoft YaHei", 10))
        self._data_source_label.setStyleSheet("color: #666666;")
        info_bar_layout.addWidget(self._data_source_label)
        
        self._last_update_label = QLabel("⏰ 更新时间: --")
        self._last_update_label.setFont(QFont("Microsoft YaHei", 10))
        self._last_update_label.setStyleSheet("color: #666666;")
        info_bar_layout.addWidget(self._last_update_label)
        
        info_bar_layout.addStretch()
        
        self._api_status_label = QLabel("")
        self._api_status_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        info_bar_layout.addWidget(self._api_status_label)
        
        main_layout.addLayout(info_bar_layout)
        
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
    
    def _on_city_selected(self, index: int):
        """下拉列表城市选择事件"""
        city = self.city_combo.currentText().strip()
        if city and city != self._current_city:
            self._current_city = city
            self._load_weather_data()
    
    def _on_search(self):
        """搜索按钮点击事件"""
        city = self.city_combo.currentText().strip()
        if not city:
            QMessageBox.warning(self, "警告", "请输入城市名称！")
            return
        
        self._current_city = city
        self._load_weather_data()
    
    def _on_refresh(self):
        """刷新按钮点击事件"""
        self._load_weather_data()
    
    def _load_weather_data(self):
        """加载天气数据"""
        self.search_btn.setEnabled(False)
        self.search_btn.setText("查询中...")
        self.refresh_btn.setEnabled(False)
        self._update_data_source_info("📡 数据来源: 正在查询...", "#FF9800")
        self._api_status_label.setText("🔄 连接中...")
        self._api_status_label.setStyleSheet("color: #FF9800;")
        
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
    
    def _update_data_source_info(self, text: str, color: str = "#666666"):
        """更新数据来源信息显示"""
        if self._data_source_label:
            self._data_source_label.setText(text)
            self._data_source_label.setStyleSheet(f"color: {color};")
    
    def _update_last_update_time(self):
        """更新最后更新时间"""
        if self._last_update_label:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._last_update_label.setText(f"⏰ 更新时间: {now}")
    
    def _on_forecast_data_ready(self, result: Dict[str, Any]):
        """预报数据准备完成"""
        self.search_btn.setEnabled(True)
        self.search_btn.setText("🔍 查询")
        self.refresh_btn.setEnabled(True)
        
        used_real_api = result.get("used_real_api", False)
        api_used = result.get("api_used")
        fallback_message = result.get("fallback_message")
        
        if used_real_api and api_used:
            self._update_data_source_info(f"📡 数据来源: 实时API ({api_used})", "#4CAF50")
            self._api_status_label.setText("✅ 在线")
            self._api_status_label.setStyleSheet("color: #4CAF50;")
        else:
            if fallback_message:
                display_msg = fallback_message
                if len(display_msg) > 80:
                    display_msg = display_msg[:80] + "..."
                self._update_data_source_info(f"⚠️ 数据来源: 本地模拟 (API错误)", "#FF9800")
                self._api_status_label.setText("❌ 离线模式")
            else:
                self._update_data_source_info("⚠️ 数据来源: 本地模拟", "#FF9800")
                self._api_status_label.setText("❌ 离线模式")
            self._api_status_label.setStyleSheet("color: #F44336;")
        
        self._update_last_update_time()
        
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
        self.search_btn.setText("🔍 查询")
        self.refresh_btn.setEnabled(True)
        self.refresh_history_btn.setEnabled(True)
        self.refresh_history_btn.setText("刷新历史数据")
        
        self._update_data_source_info(f"❌ 获取数据失败: {error_msg}", "#F44336")
        self._api_status_label.setText("❌ 错误")
        self._api_status_label.setStyleSheet("color: #F44336;")
        
        QMessageBox.critical(self, "错误", f"获取天气数据失败: {error_msg}")
    
    def _clear_layout(self, layout):
        """安全清除布局中的所有控件"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            if item.layout():
                self._clear_layout(item.layout())
    
    def _update_forecast_display(self):
        """更新预报显示"""
        self._clear_layout(self.today_card_layout)
        
        if self._forecast_data:
            today_data = self._forecast_data[0]
            today_card = WeatherCard(today_data, is_today=True)
            self.today_card_layout.addWidget(today_card)
            
            self.weather_detail = WeatherDetailWidget(today_data)
            self.today_card_layout.addWidget(self.weather_detail)
        
        self._clear_layout(self.forecast_container_layout)
        
        for weather in self._forecast_data[1:]:
            card = WeatherCard(weather, is_today=False)
            self.forecast_container_layout.addWidget(card)
        
        self.forecast_container_layout.addStretch()
    
    def _update_history_display(self):
        """更新历史显示"""
        self._clear_layout(self.history_container_layout)
        
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
