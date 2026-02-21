#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
净卸 JingUninstall - 专业的 Linux 软件卸载工具

主程序入口
"""

import sys
import os

# 添加程序安装目录到路径
INSTALL_DIR = "/opt/jing-uninstall"
if os.path.exists(INSTALL_DIR):
    sys.path.insert(0, INSTALL_DIR)
else:
    # 开发模式：使用当前目录
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.main_window import MainWindow


def setup_application():
    """设置应用程序"""
    # 启用高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 强制使用 Fusion 风格以获得一致的跨平台外观
    from PyQt6.QtWidgets import QStyleFactory
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    app.setApplicationName("JingUninstall")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("JingUninstall Team")

    # 设置全局字体
    font = QFont("Noto Sans CJK SC", 10)
    app.setFont(font)

    # 强制设置全局调色板 - 解决 ComboBox 下拉列表颜色问题
    from PyQt6.QtGui import QPalette, QColor
    global_palette = app.palette()
    global_palette.setColor(QPalette.ColorRole.Highlight, QColor(102, 126, 234))
    global_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    global_palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
    global_palette.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))
    global_palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    global_palette.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
    app.setPalette(global_palette)

    # 设置应用样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QTableWidget {
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
            gridline-color: #e0e0e0;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QTableWidget::item:selected {
            background-color: #e3f2fd;
            color: #333;
        }
        QHeaderView::section {
            background-color: #f0f0f0;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #ddd;
            font-weight: bold;
        }
        QPushButton {
            background-color: #e0e0e0;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #c0c0c0;
        }
        QLineEdit {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        QLineEdit:focus {
            border-color: #2196F3;
        }
        QComboBox {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
        }
        QComboBox:focus {
            border-color: #2196F3;
        }
        QProgressBar {
            border: 1px solid #ddd;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
        }
        QMessageBox {
            background-color: white;
        }
    """)

    return app


def main():
    """主函数"""
    app = setup_application()

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
