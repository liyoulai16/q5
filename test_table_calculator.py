#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 检查表格计算器模块是否能正确加载
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.module_manager import ModuleManager

def test_module_discovery():
    print("测试模块发现功能...")
    mm = ModuleManager()
    modules = mm.get_available_modules()
    
    print("\n发现的模块数量: %d" % len(modules))
    print("\n模块列表:")
    for module_id, module_info in modules.items():
        print("  - %s: %s" % (module_id, module_info['name']))
        print("    描述: %s" % module_info['description'])
        print("    版本: %s" % module_info['version'])
    
    # 检查是否包含表格计算器模块
    if 'table_calculator' in modules:
        print("\n表格计算器模块已成功发现!")
    else:
        print("\n表格计算器模块未被发现!")

if __name__ == '__main__':
    test_module_discovery()
