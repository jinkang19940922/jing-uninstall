#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
残留扫描对话框 - 显示残留扫描结果
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QCheckBox, QWidget, QProgressBar,
                             QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from core.residue_scan import ResidueScanner, ResidueFile, ResidueType


class ResidueScanThread(QThread):
    """残留扫描线程"""
    scan_complete = pyqtSignal(list)
    progress_update = pyqtSignal(str, int)

    def __init__(self, package_name: str):
        super().__init__()
        self.package_name = package_name

    def run(self):
        scanner = ResidueScanner()
        self.progress_update.emit(f"正在扫描 {self.package_name} 的残留...", 0)
        result = scanner.scan(self.package_name)
        self.progress_update.emit("扫描完成", 100)
        self.scan_complete.emit(result)


class ResidueDialog(QDialog):
    """残留扫描对话框"""

    # 信号：用户确认清理
    clean_confirmed = pyqtSignal(list)

    def __init__(self, package_name: str, parent=None):
        super().__init__(parent)
        self.package_name = package_name
        self.residue_files = []
        self.scanner = ResidueScanner()

        self.setWindowTitle(f"残留扫描 - {package_name}")
        self.setMinimumSize(700, 500)
        self.resize(800, 550)

        self._setup_ui()
        self._start_scan()

    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(layout)

        # 标题
        title = QLabel(f"扫描 {self.package_name} 的残留文件")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #667eea;")
        layout.addWidget(title)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("正在初始化扫描...")
        layout.addWidget(self.status_label)

        # 文件列表
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels(['选择', '路径', '类型', '大小', '安全'])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.file_table.setColumnWidth(0, 50)
        self.file_table.setColumnWidth(2, 70)
        self.file_table.setColumnWidth(3, 80)
        self.file_table.setColumnWidth(4, 50)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setEditTriggers(QTableWidget.EditTrigger.NoEdit)
        layout.addWidget(self.file_table)

        # 统计信息
        self.info_label = QLabel("共发现 0 个文件，总计 0 B")
        self.info_label.setStyleSheet("color: #666;")
        layout.addWidget(self.info_label)

        # 按钮组
        button_group = QGroupBox()
        button_layout = QHBoxLayout(button_group)
        button_layout.setContentsMargins(0, 10, 0, 0)

        # 全选/取消全选
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self._toggle_select_all)
        button_layout.addWidget(self.select_all_btn)

        self.select_all_btn.setEnabled(False)

        button_layout.addStretch()

        # 取消
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        # 清理选中
        clean_btn = QPushButton("🗑️ 清理选中")
        clean_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        clean_btn.clicked.connect(self._on_clean)
        button_layout.addWidget(clean_btn)

        layout.addWidget(button_group)

    def _start_scan(self):
        """开始扫描"""
        self.scan_thread = ResidueScanThread(self.package_name)
        self.scan_thread.scan_complete.connect(self._on_scan_complete)
        self.scan_thread.progress_update.connect(self._on_progress_update)
        self.scan_thread.start()

    def _on_progress_update(self, message: str, percent: int):
        """进度更新"""
        self.status_label.setText(message)
        self.progress_bar.setValue(percent)

    def _on_scan_complete(self, files: list):
        """扫描完成"""
        self.residue_files = files
        self._populate_table()

        count = len(files)
        total_size = self.scanner._format_size(sum(f.size for f in files))
        self.info_label.setText(f"共发现 {count} 个文件，总计 {total_size}")
        self.select_all_btn.setEnabled(count > 0)

    def _populate_table(self):
        """填充表格"""
        self.file_table.setRowCount(len(self.residue_files))

        for row, file in enumerate(self.residue_files):
            # 选择列
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(10, 0, 0, 0)
            checkbox = QCheckBox()
            checkbox.setChecked(file.is_selected)
            checkbox.stateChanged.connect(lambda state, f=file: self._on_checkbox_changed(f, state))
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.addStretch()
            self.file_table.setCellWidget(row, 0, checkbox_widget)

            # 路径
            path_item = QTableWidgetItem(file.path)
            path_item.setToolTip(file.path)
            self.file_table.setItem(row, 1, path_item)

            # 类型
            type_item = QTableWidgetItem(file.type.value)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_table.setItem(row, 2, type_item)

            # 大小
            size_item = QTableWidgetItem(file.size_str)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_table.setItem(row, 3, size_item)

            # 安全
            safe_item = QTableWidgetItem("安全" if file.is_safe_to_delete else "注意")
            safe_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if file.is_safe_to_delete:
                safe_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                safe_item.setForeground(Qt.GlobalColor.darkYellow)
            self.file_table.setItem(row, 4, safe_item)

    def _on_checkbox_changed(self, residue_file: ResidueFile, state: int):
        """复选框状态改变"""
        residue_file.is_selected = (state == Qt.CheckState.Checked.value)
        self._update_info()

    def _update_info(self):
        """更新统计信息"""
        selected = [f for f in self.residue_files if f.is_selected]
        total_size = self.scanner._format_size(sum(f.size for f in selected))
        self.info_label.setText(f"已选择 {len(selected)}/{len(self.residue_files)} 个文件，总计 {total_size}")

    def _toggle_select_all(self):
        """全选/取消全选"""
        # 检查当前是否全选
        all_selected = all(f.is_selected for f in self.residue_files)

        for f in self.residue_files:
            f.is_selected = not all_selected

        self._populate_table()
        self._update_info()

        if all_selected:
            self.select_all_btn.setText("全选")
        else:
            self.select_all_btn.setText("取消全选")

    def _on_clean(self):
        """确认清理"""
        selected = [f for f in self.residue_files if f.is_selected]

        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要清理的文件")
            return

        total_size = self.scanner._format_size(sum(f.size for f in selected))

        reply = QMessageBox.question(
            self,
            "确认清理",
            f"确定要清理选中的 {len(selected)} 个文件吗？\n\n总计：{total_size}\n\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.accept()
            self.clean_confirmed.emit(selected)

    def get_selected_files(self) -> list:
        """获取选中的文件"""
        return [f for f in self.residue_files if f.is_selected]


class BatchCleanDialog(QDialog):
    """批量清理对话框"""

    def __init__(self, residue_files: list, parent=None):
        super().__init__(parent)
        self.residue_files = residue_files
        self.scanner = ResidueScanner()

        self.setWindowTitle("批量清理残留")
        self.setMinimumSize(700, 500)
        self.resize(800, 550)

        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(layout)

        # 标题
        title = QLabel("批量清理残留文件")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #667eea;")
        layout.addWidget(title)

        # 文件列表
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels(['选择', '路径', '类型', '大小', '安全'])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.file_table.setColumnWidth(0, 50)
        self.file_table.setColumnWidth(2, 70)
        self.file_table.setColumnWidth(3, 80)
        self.file_table.setColumnWidth(4, 50)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setEditTriggers(QTableWidget.EditTrigger.NoEdit)
        layout.addWidget(self.file_table)

        # 统计信息
        self.info_label = QLabel("共发现 0 个文件，总计 0 B")
        self.info_label.setStyleSheet("color: #666;")
        layout.addWidget(self.info_label)

        # 按钮组
        button_group = QWidget()
        button_layout = QHBoxLayout(button_group)
        button_layout.setContentsMargins(0, 10, 0, 0)

        # 全选/取消全选
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self._toggle_select_all)
        button_layout.addWidget(self.select_all_btn)

        button_layout.addStretch()

        # 取消
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        # 清理选中
        clean_btn = QPushButton("清理选中")
        clean_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        clean_btn.clicked.connect(self._on_clean)
        button_layout.addWidget(clean_btn)

        layout.addWidget(button_group)

        self._update_info()

    def _populate_table(self):
        """填充表格"""
        self.file_table.setRowCount(len(self.residue_files))

        for row, file in enumerate(self.residue_files):
            # 选择列
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(10, 0, 0, 0)
            checkbox = QCheckBox()
            checkbox.setChecked(file.is_selected)
            checkbox.stateChanged.connect(lambda state, f=file: self._on_checkbox_changed(f, state))
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.addStretch()
            self.file_table.setCellWidget(row, 0, checkbox_widget)

            # 路径
            path_item = QTableWidgetItem(file.path)
            path_item.setToolTip(file.path)
            self.file_table.setItem(row, 1, path_item)

            # 类型
            type_item = QTableWidgetItem(file.type.value)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_table.setItem(row, 2, type_item)

            # 大小
            size_item = QTableWidgetItem(file.size_str)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_table.setItem(row, 3, size_item)

            # 安全
            safe_item = QTableWidgetItem("安全" if file.is_safe_to_delete else "注意")
            safe_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if file.is_safe_to_delete:
                safe_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                safe_item.setForeground(Qt.GlobalColor.darkYellow)
            self.file_table.setItem(row, 4, safe_item)

    def _on_checkbox_changed(self, residue_file: ResidueFile, state: int):
        """复选框状态改变"""
        residue_file.is_selected = (state == Qt.CheckState.Checked.value)
        self._update_info()

    def _update_info(self):
        """更新统计信息"""
        selected = [f for f in self.residue_files if f.is_selected]
        total_size = self.scanner._format_size(sum(f.size for f in selected))
        self.info_label.setText(f"已选择 {len(selected)}/{len(self.residue_files)} 个文件，总计 {total_size}")

    def _toggle_select_all(self):
        """全选/取消全选"""
        all_selected = all(f.is_selected for f in self.residue_files)

        for f in self.residue_files:
            f.is_selected = not all_selected

        self._populate_table()
        self._update_info()

        if all_selected:
            self.select_all_btn.setText("全选")
        else:
            self.select_all_btn.setText("取消全选")

    def _on_clean(self):
        """确认清理"""
        selected = [f for f in self.residue_files if f.is_selected]

        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要清理的文件")
            return

        total_size = self.scanner._format_size(sum(f.size for f in selected))

        reply = QMessageBox.question(
            self,
            "确认清理",
            f"确定要清理选中的 {len(selected)} 个文件吗？\n\n总计：{total_size}\n\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.accept()

    def get_selected_files(self) -> list:
        """获取选中的文件"""
        return [f for f in self.residue_files if f.is_selected]
