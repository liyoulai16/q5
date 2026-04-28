#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块管理器
负责发现、加载和管理应用程序的功能模块
"""

import os
import sys
import importlib
import importlib.util
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable


class ModuleCategory:
    """
    模块分类常量
    """
    OFFICE_TOOLS = "office_tools"
    LIFE_TOOLS = "life_tools"
    DATA_MANAGEMENT = "data_management"
    CORE_FRAMEWORK = "core_framework"
    
    CATEGORY_NAMES = {
        OFFICE_TOOLS: "办公工具",
        LIFE_TOOLS: "生活工具",
        DATA_MANAGEMENT: "数据管理",
        CORE_FRAMEWORK: "核心框架"
    }
    
    CATEGORY_ICONS = {
        OFFICE_TOOLS: "📋",
        LIFE_TOOLS: "🏠",
        DATA_MANAGEMENT: "🗄️",
        CORE_FRAMEWORK: "⚙️"
    }


class BaseModule(ABC):
    """
    模块基类
   所有自定义模块都应该继承此类
    """
    
    def __init__(self):
        self._loaded = False
        self._widget = None
    
    @property
    @abstractmethod
    def module_id(self) -> str:
        """模块唯一标识符"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """模块显示名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """模块描述"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """模块版本"""
        pass
    
    @property
    def category(self) -> str:
        """模块分类，默认为办公工具"""
        return ModuleCategory.OFFICE_TOOLS
    
    @property
    def icon(self) -> Optional[str]:
        """模块图标路径（可选）"""
        return None
    
    @property
    def author(self) -> Optional[str]:
        """模块作者（可选）"""
        return None
    
    def load(self) -> bool:
        """
        加载模块
        在此执行初始化操作
        """
        if not self._loaded:
            try:
                self._on_load()
                self._loaded = True
                return True
            except Exception as e:
                print(f"加载模块 {self.module_id} 失败: {e}")
                return False
        return True
    
    def unload(self) -> bool:
        """
        卸载模块
        在此执行清理操作
        """
        if self._loaded:
            try:
                self._on_unload()
                self._loaded = False
                if self._widget:
                    self._widget.deleteLater()
                    self._widget = None
                return True
            except Exception as e:
                print(f"卸载模块 {self.module_id} 失败: {e}")
                return False
        return True
    
    @abstractmethod
    def _on_load(self) -> None:
        """
        模块加载时的具体实现
        子类应该重写此方法
        """
        pass
    
    @abstractmethod
    def _on_unload(self) -> None:
        """
        模块卸载时的具体实现
        子类应该重写此方法
        """
        pass
    
    @abstractmethod
    def _create_widget(self) -> Any:
        """
        创建模块的主界面组件
        子类应该重写此方法
        返回一个QtWidget实例
        """
        pass
    
    def get_widget(self) -> Any:
        """
        获取模块的界面组件
        如果组件不存在则创建
        """
        if not self._widget:
            self._widget = self._create_widget()
        return self._widget
    
    def is_loaded(self) -> bool:
        """检查模块是否已加载"""
        return self._loaded
    
    def get_info(self) -> Dict[str, Any]:
        """获取模块信息"""
        return {
            'module_id': self.module_id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'icon': self.icon,
            'author': self.author,
            'loaded': self._loaded
        }


class LazyModuleProxy:
    """
    延迟加载模块代理
    在实际需要时才加载完整模块
    """
    
    def __init__(self, module_id: str, module_path: str, module_file: str):
        self._module_id = module_id
        self._module_path = module_path
        self._module_file = module_file
        self._module_class: Optional[type] = None
        self._module_instance: Optional[BaseModule] = None
        self._metadata_loaded = False
        
        self._cached_metadata: Dict[str, Any] = {
            'module_id': module_id,
            'name': module_id,
            'description': '',
            'version': '1.0.0',
            'category': ModuleCategory.OFFICE_TOOLS,
            'icon': None,
            'author': None
        }
    
    def _load_module_class(self) -> bool:
        """
        加载模块类（仅导入，不实例化）
        """
        if self._module_class is not None:
            return True
        
        try:
            module_name = os.path.basename(self._module_path)
            module_spec = importlib.util.spec_from_file_location(
                f"modules.{module_name}.{module_name}_module",
                self._module_file
            )
            
            if module_spec and module_spec.loader:
                module = importlib.util.module_from_spec(module_spec)
                sys.modules[module_spec.name] = module
                module_spec.loader.exec_module(module)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseModule) and 
                        attr != BaseModule):
                        self._module_class = attr
                        return True
                        
        except Exception as e:
            print(f"加载模块类 {self._module_id} 失败: {e}")
        
        return False
    
    def _load_metadata(self) -> None:
        """
        加载模块元数据（轻量级加载，仅获取基本信息）
        """
        if self._metadata_loaded:
            return
        
        if self._load_module_class() and self._module_class:
            try:
                temp_instance = self._module_class()
                self._cached_metadata = {
                    'module_id': temp_instance.module_id,
                    'name': temp_instance.name,
                    'description': temp_instance.description,
                    'version': temp_instance.version,
                    'category': temp_instance.category,
                    'icon': temp_instance.icon,
                    'author': temp_instance.author
                }
                self._metadata_loaded = True
            except Exception as e:
                print(f"加载模块元数据 {self._module_id} 失败: {e}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取模块元数据
        """
        self._load_metadata()
        return self._cached_metadata.copy()
    
    def get_instance(self, force_reload: bool = False) -> Optional[BaseModule]:
        """
        获取模块实例（完全加载）
        """
        if self._module_instance is not None and not force_reload:
            return self._module_instance
        
        if self._load_module_class() and self._module_class:
            try:
                self._module_instance = self._module_class()
                return self._module_instance
            except Exception as e:
                print(f"创建模块实例 {self._module_id} 失败: {e}")
        
        return None
    
    def is_loaded(self) -> bool:
        """
        检查模块是否已完全加载
        """
        return self._module_instance is not None
    
    def is_metadata_loaded(self) -> bool:
        """
        检查元数据是否已加载
        """
        return self._metadata_loaded


class ModuleManager:
    """
    模块管理器
    负责发现、加载和管理所有模块
    支持延迟加载：只在实际使用时才加载完整模块
    """
    
    def __init__(self, modules_dir: str = None):
        if modules_dir is None:
            modules_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        
        self.modules_dir = modules_dir
        self._module_proxies: Dict[str, LazyModuleProxy] = {}
        self._loaded_modules: Dict[str, BaseModule] = {}
        
        self._discover_modules()
    
    def _discover_modules(self) -> None:
        """
        发现可用的模块
        扫描modules目录下的所有子目录，查找符合规范的模块
        使用延迟加载：仅创建代理，不实际导入模块
        """
        if not os.path.exists(self.modules_dir):
            print(f"模块目录不存在: {self.modules_dir}")
            return
        
        for item in os.listdir(self.modules_dir):
            item_path = os.path.join(self.modules_dir, item)
            
            if os.path.isdir(item_path) and not item.startswith('_'):
                module_file = os.path.join(item_path, f"{item}_module.py")
                if os.path.exists(module_file):
                    self._register_module_lazy(item, item_path, module_file)
    
    def _register_module_lazy(self, module_name: str, module_path: str, module_file: str) -> None:
        """
        延迟注册模块（仅创建代理，不实际加载）
        """
        try:
            module_id = module_name
            proxy = LazyModuleProxy(module_id, module_path, module_file)
            self._module_proxies[module_id] = proxy
            print(f"发现模块: {module_name} (延迟加载)")
        except Exception as e:
            print(f"注册模块代理 {module_name} 失败: {e}")
    
    def get_available_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有可用模块的信息
        延迟加载：仅在需要时才加载元数据
        """
        result = {}
        for module_id, proxy in self._module_proxies.items():
            result[module_id] = proxy.get_metadata()
        return result
    
    def load_module(self, module_id: str) -> Optional[BaseModule]:
        """
        加载指定的模块（完全加载，包括初始化）
        """
        if module_id in self._loaded_modules:
            return self._loaded_modules[module_id]
        
        if module_id not in self._module_proxies:
            print(f"模块不存在: {module_id}")
            return None
        
        proxy = self._module_proxies[module_id]
        module_instance = proxy.get_instance()
        
        if module_instance:
            if module_instance.load():
                self._loaded_modules[module_id] = module_instance
                print(f"成功加载模块: {module_id}")
                return module_instance
            else:
                print(f"模块加载失败: {module_id}")
                return None
        
        return None
    
    def unload_module(self, module_id: str) -> bool:
        """
        卸载指定的模块
        """
        if module_id not in self._loaded_modules:
            return True
        
        module_instance = self._loaded_modules[module_id]
        if module_instance.unload():
            del self._loaded_modules[module_id]
            if module_id in self._module_proxies:
                self._module_proxies[module_id]._module_instance = None
            print(f"成功卸载模块: {module_id}")
            return True
        
        return False
    
    def unload_all_modules(self) -> bool:
        """
        卸载所有已加载的模块
        """
        all_success = True
        module_ids = list(self._loaded_modules.keys())
        
        for module_id in module_ids:
            if not self.unload_module(module_id):
                all_success = False
        
        return all_success
    
    def get_loaded_module(self, module_id: str) -> Optional[BaseModule]:
        """
        获取已加载的模块实例
        """
        return self._loaded_modules.get(module_id)
    
    def is_module_loaded(self, module_id: str) -> bool:
        """
        检查模块是否已完全加载
        """
        return module_id in self._loaded_modules
    
    def get_available_categories(self) -> List[str]:
        """
        获取所有可用的模块分类
        """
        categories = set()
        for proxy in self._module_proxies.values():
            metadata = proxy.get_metadata()
            categories.add(metadata.get('category', ModuleCategory.OFFICE_TOOLS))
        return list(categories)
    
    def get_modules_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """
        按分类获取模块信息
        """
        filtered_modules = {}
        for module_id, proxy in self._module_proxies.items():
            metadata = proxy.get_metadata()
            if metadata.get('category') == category:
                filtered_modules[module_id] = metadata.copy()
        return filtered_modules
    
    def get_module_metadata(self, module_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定模块的元数据（轻量级，不加载完整模块）
        """
        if module_id in self._module_proxies:
            return self._module_proxies[module_id].get_metadata()
        return None
