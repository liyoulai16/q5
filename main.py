#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多功能桌面效率工具套件
基于PyQt6的桌面应用，支持模块化扩展
"""

import sys
import os

from PyQt6.QtWidgets import QApplication, QMessageBox

from core.main_window import MainWindow
from core.login_dialog import LoginDialog

def main():
    app = QApplication(sys.argv)
    
    login_dialog = LoginDialog()
    
    if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
        if login_dialog.is_authenticated():
            window = MainWindow()
            window.show()
            
            sys.exit(app.exec())
    else:
        QMessageBox.information(None, "提示", "登录已取消，程序将退出。")
        sys.exit(0)

if __name__ == '__main__':
    main()
