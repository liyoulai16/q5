#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多功能桌面效率工具套件
基于PyQt6的桌面应用，支持模块化扩展
"""

import sys
import os

from PyQt6.QtWidgets import QApplication

from core.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
