#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口 - 应用程序主界面

功能特性：
- 现代化界面设计
- 渐变紫色主题
- 流畅的动画效果
- 完整的卸载功能
"""

import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QLabel, QComboBox,
                             QStatusBar, QMenu, QMessageBox, QFrame,
                             QProgressBar, QStyleFactory)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QColor

from core.scanner import PackageScanner, Package, PackageSource
from core.uninstaller import Uninstaller
from core.residue_scan import ResidueScanner
from core.cleaner import Cleaner

from ui.package_list import PackageListWidget
from ui.residue_dialog import ResidueDialog
from ui.progress_dialog import ProgressDialog

from backends.apt_backend import APTBackend
from backends.snap_backend import SnapBackend
from backends.flatpak_backend import FlatpakBackend
from backends.appimage_backend import AppImageBackend


class ScanThread(QThread):
    """扫描线程"""
    scan_complete = pyqtSignal(list)
    progress_update = pyqtSignal(str, int)

    def __init__(self, scanner: PackageScanner):
        super().__init__()
        self.scanner = scanner
        self._progress_counter = 0

    def run(self):
        def progress_cb(msg, pct):
            self._progress_counter += 1
            if self._progress_counter % 10 == 0 or pct == 100:
                self.progress_update.emit(msg, pct)

        self.scanner.set_progress_callback(progress_cb)
        packages = self.scanner.scan_all()
        self.scan_complete.emit(packages)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        # 初始化扫描器，启用跳过系统包
        self.scanner = PackageScanner(skip_system_packages=True)
        self.uninstaller = Uninstaller()
        self.packages = []

        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._connect_signals()

        QTimer.singleShot(300, self._start_scan)

    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("净卸 JingUninstall")
        self.setMinimumSize(1000, 650)
        self.resize(1100, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部标题栏
        self._setup_title_bar(main_layout)
        # 进度条
        self._setup_progress_bar(main_layout)
        # 工具栏
        self._setup_toolbar(main_layout)
        # 软件列表
        self._setup_package_list(main_layout)
        # 底部操作栏
        self._setup_bottom_bar(main_layout)

    def _setup_title_bar(self, layout):
        """设置标题栏"""
        title_frame = QFrame()
        title_frame.setFixedHeight(55)
        title_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-bottom: 1px solid #ddd;
            }
        """)

        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(20, 0, 20, 0)

        title_label = QLabel("净卸 JingUninstall")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px;")
        title_layout.addWidget(version_label)

        layout.addWidget(title_frame)

    def _setup_progress_bar(self, layout):
        """设置进度条"""
        progress_frame = QFrame()
        progress_frame.setFixedHeight(45)
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
            }
        """)

        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(20, 6, 20, 6)
        progress_layout.setSpacing(4)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #e0e0e0;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #666; font-size: 12px;")
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(progress_frame)

    def _setup_toolbar(self, layout):
        """设置工具栏"""
        toolbar_frame = QFrame()
        toolbar_frame.setFixedHeight(65)
        toolbar_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
            }
        """)

        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(20, 10, 20, 10)
        toolbar_layout.setSpacing(12)

        # 搜索标签 - 使用文本代替 emoji
        search_label = QLabel("搜索")
        search_label.setStyleSheet("color: #666; font-size: 14px; font-weight: bold;")
        search_label.setFixedWidth(45)
        toolbar_layout.addWidget(search_label)

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索软件名称...")
        self.search_input.setMinimumWidth(250)
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 18px;
                background-color: #f5f5f5;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background-color: white;
            }
        """)
        toolbar_layout.addWidget(self.search_input)

        # 来源过滤器
        self.source_filter = QComboBox()
        self.source_filter.addItems(["全部来源", "APT", "Snap", "Flatpak", "AppImage"])
        self.source_filter.setFixedHeight(36)
        self.source_filter.setFixedWidth(130)
        
        # 使用 Fusion 风格确保样式一致
        self.source_filter.setStyle(QStyleFactory.create("Fusion"))
        
        # 设置下拉列表视图的调色板 - 关键修复
        view = self.source_filter.view()
        from PyQt6.QtGui import QPalette, QColor
        palette = view.palette()
        # 设置选中/悬停颜色 - 紫色背景 + 白色文字
        palette.setColor(QPalette.ColorRole.Highlight, QColor(102, 126, 234))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        # 设置默认颜色 - 白色背景 + 黑色文字
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        view.setPalette(palette)
        view.setAutoFillBackground(True)
        
        # 设置样式表
        self.source_filter.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 18px;
                background-color: white;
                font-size: 13px;
                color: black;
            }
            QComboBox:focus {
                border-color: #667eea;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid #667eea;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #e0e0e0;
                background-color: white;
                border-radius: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                min-height: 30px;
                background-color: white;
                color: black;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #667eea;
                color: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #667eea;
                color: white;
            }
        """)
        toolbar_layout.addWidget(self.source_filter)

        toolbar_layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setMinimumWidth(90)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 18px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd6, stop:1 #6a4190);
            }
        """)
        refresh_btn.clicked.connect(self._start_scan)
        toolbar_layout.addWidget(refresh_btn)

        layout.addWidget(toolbar_frame)

    def _setup_package_list(self, layout):
        """设置软件列表"""
        self.package_list = PackageListWidget()
        layout.addWidget(self.package_list)

    def _setup_bottom_bar(self, layout):
        """设置底部操作栏"""
        bottom_frame = QFrame()
        bottom_frame.setFixedHeight(65)
        bottom_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #e0e0e0;
            }
        """)

        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(20, 10, 20, 10)
        bottom_layout.setSpacing(12)

        self.info_label = QLabel("共 0 个软件 | 已选择 0 个")
        self.info_label.setStyleSheet("font-size: 13px; color: #666;")
        bottom_layout.addWidget(self.info_label)

        bottom_layout.addStretch()

        self.uninstall_btn = QPushButton("卸载")
        self.uninstall_btn.setFixedHeight(40)
        self.uninstall_btn.setMinimumWidth(100)
        self.uninstall_btn.setStyleSheet(self._get_button_style("#f44336", "#da190b"))
        bottom_layout.addWidget(self.uninstall_btn)

        self.force_uninstall_btn = QPushButton("强制卸载")
        self.force_uninstall_btn.setFixedHeight(40)
        self.force_uninstall_btn.setMinimumWidth(100)
        self.force_uninstall_btn.setStyleSheet(self._get_button_style("#ff9800", "#f57c00"))
        bottom_layout.addWidget(self.force_uninstall_btn)

        self.scan_residue_btn = QPushButton("扫描残留")
        self.scan_residue_btn.setFixedHeight(40)
        self.scan_residue_btn.setMinimumWidth(100)
        self.scan_residue_btn.setStyleSheet(self._get_button_style("#2196F3", "#1976D2"))
        bottom_layout.addWidget(self.scan_residue_btn)

        layout.addWidget(bottom_frame)

    def _get_button_style(self, normal, hover):
        """获取按钮样式"""
        return f"""
            QPushButton {{
                background-color: {normal};
                color: white;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                opacity: 0.8;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #999;
            }}
        """

    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
            }
            QMenuBar::item {
                padding: 6px 12px;
                background-color: transparent;
            }
            QMenuBar::item:selected {
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """)

        file_menu = menubar.addMenu("文件 (&F)")
        refresh_action = QAction("刷新 (&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._start_scan)
        file_menu.addAction(refresh_action)
        file_menu.addSeparator()
        exit_action = QAction("退出 (&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("编辑 (&E)")
        select_all_action = QAction("全选 (&A)", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.package_list.select_all)
        edit_menu.addAction(select_all_action)
        deselect_all_action = QAction("取消全选 (&D)", self)
        deselect_all_action.setShortcut("Ctrl+Shift+A")
        deselect_all_action.triggered.connect(self.package_list.deselect_all)
        edit_menu.addAction(deselect_all_action)
        invert_action = QAction("反选 (&I)", self)
        invert_action.setShortcut("Ctrl+I")
        invert_action.triggered.connect(self.package_list.invert_selection)
        edit_menu.addAction(invert_action)

        tools_menu = menubar.addMenu("工具 (&T)")
        clean_residual_action = QAction("批量清理残留 (&C)", self)
        clean_residual_action.triggered.connect(self._batch_clean)
        tools_menu.addAction(clean_residual_action)

        help_menu = menubar.addMenu("帮助 (&H)")
        about_action = QAction("关于 (&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #fafafa;
                border-top: 1px solid #e0e0e0;
                color: #666;
            }
        """)
        self.status_bar.showMessage("就绪")

    def _connect_signals(self):
        """连接信号"""
        self.package_list.selection_changed.connect(self._on_selection_changed)
        self.package_list.package_double_clicked.connect(self._on_package_double_clicked)
        self.search_input.textChanged.connect(self._filter_packages)
        self.uninstall_btn.clicked.connect(self._uninstall_selected)
        self.force_uninstall_btn.clicked.connect(self._force_uninstall_selected)
        self.scan_residue_btn.clicked.connect(self._scan_residue_selected)

    def _start_scan(self):
        """开始扫描"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(True)
        self.progress_label.setText("正在初始化扫描...")

        self.status_bar.showMessage("正在扫描...")
        self.uninstall_btn.setEnabled(False)
        self.force_uninstall_btn.setEnabled(False)
        self.scan_residue_btn.setEnabled(False)

        self.scan_thread = ScanThread(self.scanner)
        self.scan_thread.scan_complete.connect(self._on_scan_complete, Qt.ConnectionType.QueuedConnection)
        self.scan_thread.progress_update.connect(self._on_progress_update, Qt.ConnectionType.QueuedConnection)
        self.scan_thread.start()

    def _on_progress_update(self, message: str, percent: int):
        """进度更新"""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)
        self.status_bar.showMessage(f"{message} ({percent}%)")

    def _on_scan_complete(self, packages: list):
        """扫描完成"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        self.packages = packages
        self.package_list.load_packages(packages)
        self._update_info()
        self.status_bar.showMessage(f"扫描完成，共 {len(packages)} 个软件")

    def _on_selection_changed(self, selected: list):
        """选择改变"""
        self._update_info()
        has_selection = len(selected) > 0
        self.uninstall_btn.setEnabled(has_selection)
        self.force_uninstall_btn.setEnabled(has_selection)
        self.scan_residue_btn.setEnabled(has_selection and len(selected) == 1)

    def _update_info(self):
        """更新信息标签"""
        total = self.package_list.get_package_count()
        selected = self.package_list.get_selected_count()
        self.info_label.setText(f"共 {total} 个软件 | 已选择 {selected} 个")

    def _filter_packages(self, text: str = None):
        """过滤软件列表"""
        search_text = self.search_input.text().lower()
        source_text = self.source_filter.currentText()

        filtered = []
        for package in self.packages:
            if source_text != "全部来源":
                if package.source.value != source_text:
                    continue
            if search_text:
                if (search_text not in package.name.lower() and
                        search_text not in package.display_name.lower()):
                    continue
            filtered.append(package)

        self.package_list.load_packages(filtered)

    def _on_package_double_clicked(self, package: Package):
        """双击软件"""
        pass

    def _uninstall_selected(self):
        """卸载选中的软件"""
        selected = self.package_list.get_selected_packages()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要卸载的软件")
            return

        if len(selected) == 1:
            pkg = selected[0]
            msg = f"确定要卸载 {pkg.display_name} 吗？\n\n来源：{pkg.source.value}\n大小：{pkg.size}"
        else:
            msg = f"确定要卸载选中的 {len(selected)} 个软件吗？"

        reply = QMessageBox.question(self, "确认卸载", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.progress_dialog = ProgressDialog("正在卸载...")
        self.progress_dialog.show()

        def uninstall_task(progress_cb, error_cb):
            for i, pkg in enumerate(selected):
                progress_cb(f"正在卸载 {pkg.display_name}...", int(i / len(selected) * 100))
                success, msg = self.uninstaller.uninstall(pkg)
                if not success:
                    error_cb(msg)
            return "卸载完成"

        self.progress_dialog.start_task(uninstall_task)
        self.progress_dialog.finished.connect(self._on_uninstall_finished)

    def _force_uninstall_selected(self):
        """强制卸载选中的软件"""
        selected = self.package_list.get_selected_packages()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要强制卸载的软件")
            return

        msg = "警告：强制卸载不会经过包管理器，可能导致系统状态不一致！\n\n仅在正常卸载失败时使用此功能。\n\n"
        msg += f"确定要强制卸载选中的 {len(selected)} 个软件吗？"

        reply = QMessageBox.warning(self, "强制卸载警告", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.progress_dialog = ProgressDialog("正在强制卸载...")
        self.progress_dialog.show()

        def force_uninstall_task(progress_cb, error_cb):
            for i, pkg in enumerate(selected):
                progress_cb(f"正在强制卸载 {pkg.display_name}...", int(i / len(selected) * 100))
                if pkg.source == PackageSource.APT:
                    success, msg = self.uninstaller.force_remove_package(pkg)
                else:
                    success, msg = self.uninstaller.uninstall(pkg, force=True)
                if not success:
                    error_cb(msg)
            return "强制卸载完成"

        self.progress_dialog.start_task(force_uninstall_task)
        self.progress_dialog.finished.connect(self._on_uninstall_finished)

    def _scan_residue_selected(self):
        """扫描选中软件的残留"""
        selected = self.package_list.get_selected_packages()
        if len(selected) != 1:
            QMessageBox.warning(self, "提示", "请选择一个软件来扫描残留")
            return

        package = selected[0]
        self.residue_dialog = ResidueDialog(package.name)
        self.residue_dialog.clean_confirmed.connect(lambda files: self._clean_residue(package, files))
        self.residue_dialog.exec()

    def _clean_residue(self, package: Package, files: list):
        """清理残留"""
        self.progress_dialog = ProgressDialog(f"正在清理 {package.name} 的残留...")
        self.progress_dialog.show()

        def clean_task(progress_cb, error_cb):
            cleaner = Cleaner()
            cleaner.set_progress_callback(progress_cb)
            success, deleted, size = cleaner.clean(files)
            if success:
                return f"已清理 {deleted} 个文件"
            else:
                error_cb("清理失败")
                return "清理失败"

        self.progress_dialog.start_task(clean_task)

    def _batch_clean(self):
        """批量清理残留"""
        selected = self.package_list.get_selected_packages()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要清理残留的软件")
            return

        # 收集所有残留文件
        all_residue_files = []
        scanner = ResidueScanner()

        for package in selected:
            residue = scanner.scan(package.name)
            all_residue_files.extend(residue)

        if not all_residue_files:
            QMessageBox.information(self, "提示", "未发现任何残留文件")
            return

        # 显示批量清理对话框
        from ui.residue_dialog import BatchCleanDialog
        dialog = BatchCleanDialog(all_residue_files)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_files = dialog.get_selected_files()
            if selected_files:
                self.progress_dialog = ProgressDialog("正在批量清理残留...")
                self.progress_dialog.show()

                def clean_task(progress_cb, error_cb):
                    cleaner = Cleaner()
                    cleaner.set_progress_callback(progress_cb)
                    success, deleted, size = cleaner.clean(selected_files)
                    if success:
                        return f"已清理 {deleted} 个文件"
                    else:
                        error_cb("清理失败")
                        return "清理失败"

                self.progress_dialog.start_task(clean_task)

    def _on_uninstall_finished(self):
        """卸载完成"""
        self._start_scan()

    def _show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2 style="color: #667eea;">净卸 JingUninstall</h2>
        <p>版本：1.0.0</p>
        <p>一款专业的 Linux 软件卸载工具</p>
        <hr style="border: 1px solid #e0e0e0;">
        <p><b>功能特点：</b></p>
        <ul>
            <li>支持 APT/Snap/Flatpak/AppImage</li>
            <li>彻底清理残留文件和配置</li>
            <li>强制卸载功能</li>
            <li>批量操作支持</li>
        </ul>
        <hr style="border: 1px solid #e0e0e0;">
        <p style="color: #999;">© 2025 JingUninstall Team</p>
        """
        QMessageBox.about(self, "关于 净卸", about_text)
