#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件批量重命名模块修复
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)

try:
    from modules.module_manager import ModuleManager, ModuleCategory
    
    print("=" * 60)
    print("测试文件批量重命名模块修复")
    print("=" * 60)
    
    mm = ModuleManager()
    
    if 'file_renamer' not in mm.get_available_modules():
        print("ERROR: 模块未被发现!")
        sys.exit(1)
    
    print("\n1. 加载模块...")
    module = mm.load_module('file_renamer')
    if not module:
        print("ERROR: 模块加载失败!")
        sys.exit(1)
    print("   OK: 模块加载成功")
    
    print("\n2. 创建 widget (这是之前崩溃的地方)...")
    try:
        widget = module.get_widget()
        print("   OK: Widget 创建成功!")
        print(f"   Widget 类型: {type(widget).__name__}")
    except Exception as e:
        print(f"   ERROR: Widget 创建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("修复验证成功!")
    print("=" * 60)
    print("\n问题说明:")
    print("  原始错误: QButtonGroup(parent) 的 parent 参数需要 QObject 类型")
    print("  FileRenamerModule 继承自 BaseModule，不是 QObject 的子类")
    print("  修复方法: 将 QButtonGroup(self) 改为 QButtonGroup()")
    print("\n修复的位置:")
    print("  - _create_delete_group() 方法 (删除字符组)")
    print("  - _create_case_group() 方法 (大小写转换组)")
    print("  - _create_extension_group() 方法 (扩展名修改组)")
        
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
