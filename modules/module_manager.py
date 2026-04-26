#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块管理器
负责发现、加载和管理应用程序的功能模块
"""

import os
import sys
import importlib
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


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


class ModuleManager:
    """
    模块管理器
    负责发现、加载和管理所有模块
    """
    
    def __init__(self, modules_dir: str = None):
        if modules_dir is None:
            modules_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        
        self.modules_dir = modules_dir
        self._available_modules: Dict[str, Dict[str, Any]] = {}
        self._loaded_modules: Dict[str, BaseModule] = {}
        self._module_classes: Dict[str, type] = {}
        
        self._discover_modules()
    
    def _discover_modules(self) -> None:
        """
        发现可用的模块
        扫描modules目录下的所有子目录，查找符合规范的模块
        """
        if not os.path.exists(self.modules_dir):
            print(f"模块目录不存在: {self.modules_dir}")
            return
        
        for item in os.listdir(self.modules_dir):
            item_path = os.path.join(self.modules_dir, item)
            
            if os.path.isdir(item_path) and not item.startswith('_'):
                module_file = os.path.join(item_path, f"{item}_module.py")
                if os.path.exists(module_file):
                    self._register_module(item, item_path)
    
    def _register_module(self, module_name: str, module_path: str) -> None:
        """
        注册一个模块
        """
        try:
            module_file = os.path.join(module_path, f"{module_name}_module.py")
            module_spec = importlib.util.spec_from_file_location(
                f"modules.{module_name}.{module_name}_module",
                module_file
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
                        
                        temp_instance = attr()
                        module_id = temp_instance.module_id
                        
                        self._module_classes[module_id] = attr
                        self._available_modules[module_id] = {
                            'name': temp_instance.name,
                            'description': temp_instance.description,
                            'version': temp_instance.version,
                            'icon': temp_instance.icon,
                            'author': temp_instance.author,
                            'module_class': attr
                        }
                        
                        print(f"发现模块: {temp_instance.name} ({module_id})")
                        break
                        
        except Exception as e:
            print(f"注册模块 {module_name} 失败: {e}")
    
    def get_available_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有可用模块的信息
        """
        return self._available_modules.copy()
    
    def load_module(self, module_id: str) -> Optional[BaseModule]:
        """
        加载指定的模块
        """
        if module_id in self._loaded_modules:
            return self._loaded_modules[module_id]
        
        if module_id not in self._available_modules:
            print(f"模块不存在: {module_id}")
            return None
        
        try:
            module_class = self._module_classes[module_id]
            module_instance = module_class()
            
            if module_instance.load():
                self._loaded_modules[module_id] = module_instance
                print(f"成功加载模块: {module_id}")
                return module_instance
            else:
                print(f"模块加载失败: {module_id}")
                return None
                
        except Exception as e:
            print(f"加载模块 {module_id} 时发生错误: {e}")
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
        检查模块是否已加载
        """
        return module_id in self._loaded_modules
